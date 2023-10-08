import datetime
import json
import os
import time

import boto3
from azure.ai.formrecognizer import DocumentField, AddressValue, DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import pika

load_dotenv()

amqp_config = {
    "host": os.getenv('AMQP_HOST', 'rabbitmq'),
    "port": os.getenv('AMQP_PORT', '5672'),
    "queue_prefix": os.getenv('AMQP_QUEUE_PREFIX', 'receipts')
}

amqp_config["processed_queue"] = f'{amqp_config["queue_prefix"]}_processed'
amqp_config["unprocessed_queue"] = f'{amqp_config["queue_prefix"]}_unprocessed'

s3_config = {
    "access_key_id": os.getenv('S3_ACCESS_KEY_ID'),
    "secret_access_key": os.getenv('S3_SECRET_ACCESS_KEY'),
    "region": os.getenv('S3_REGION', 'us-east-1'),
    "bucket_name": os.getenv('S3_BUCKET_NAME'),
    "endpoint_url": os.getenv('S3_ENDPOINT_URL'),
    "path": os.getenv('S3_PATH', 'receipts')
}

s3_session = boto3.session.Session()
s3_client = s3_session.client(
    's3',
    aws_access_key_id=s3_config["access_key_id"],
    aws_secret_access_key=s3_config["secret_access_key"],
    region_name=s3_config["region"],
    endpoint_url=s3_config["endpoint_url"]
)

azure_config = {
    "endpoint_url": os.getenv('AZURE_ENDPOINT_URL'),
    "key": os.getenv('AZURE_KEY')
}

def connect_to_amqp(host, port=5672, queue: any = 'unspecified'):
    if isinstance(queue, str):
        queue = [queue]

    print(' [*] Connecting to server ...')

    failure_count = 0
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port))
            channel = connection.channel()
            for q in queue:
                channel.queue_declare(queue=q, durable=True)
            print(' [*] Connected to server.')
            break
        except pika.exceptions.AMQPConnectionError as e:
            handle_amqp_connection_error(e, failure_count)
            failure_count += 1
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            break

    return connection, channel

def handle_amqp_connection_error(e, failure_count):
    sleep_time = 5 + (5 * failure_count)
    print(f' [*] Connection failed. Sleeping for {sleep_time} seconds.')
    time.sleep(sleep_time)
    if failure_count >= 5:
        print(' [*] Maximum retry limit reached.')
        raise Exception("Unable to connect after 5 attempts")

def list_s3_files(bucket=s3_config["bucket_name"]):
    response = s3_client.list_objects(Bucket=bucket)
    for obj in response['Contents']:
        print(obj['Key'])

def get_s3_file(bucket, path, file):
    save_path = f'/tmp/{file}'
    s3_client.download_file(
        Bucket=bucket,
        Key=f'{path}/{file}',
        Filename=save_path
    )
    return save_path

def delete_tmp_file(file):
    os.remove(f'/tmp/{file}')

def simplify_document_field(field):
    if isinstance(field.value, AddressValue):
        return {"value": vars(field.value), "confidence": field.confidence}
    elif isinstance(field.value, datetime.date):
        return {"value": field.value.strftime('%Y-%m-%d'), "confidence": field.confidence}
    else:
        return {"value": field.value, "confidence": field.confidence}

def simplify_receipt_data(receipt_data):
    for key in receipt_data:
        if isinstance(receipt_data[key], DocumentField):
            receipt_data[key] = simplify_document_field(receipt_data[key])
        elif isinstance(receipt_data[key], list):
            for i, item in enumerate(receipt_data[key]):
                for sub_key in item:
                    if isinstance(item[sub_key], DocumentField):
                        item[sub_key] = simplify_document_field(item[sub_key])
    return receipt_data


def analyze_receipt(file):
    endpoint = azure_config['endpoint_url']
    key = azure_config['key']

    document_analysis_client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    f = open(file, 'rb')

    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-receipt", document=f, locale="en-US"
    )
    analysis = poller.result()

    receipt = analysis.documents[0]

    items = []

    if receipt.fields.get("Items"):
        for idx, item in enumerate(receipt.fields.get("Items").value):
            item_description = item.value.get("Description")
            item_quantity = item.value.get("Quantity") or 1
            item_total_price = item.value.get("TotalPrice")

            item_price = item.value.get("Price") or (item_quantity == 1 and item_total_price)

            items.append({
                "item_description": item_description,
                "item_quantity": item_quantity,
                "item_price": item_price,
                "item_total_price": item_total_price
            })

    document = analysis.documents[0]

    receipt_data = {
        "receipt_type": document.doc_type,
        "merchant_name": document.fields.get("MerchantName"),
        "merchant_address": document.fields.get("MerchantAddress"),
        "transaction_date": document.fields.get("TransactionDate"),
        "items": items,
        "subtotal": document.fields.get("Subtotal"),
        "tax": document.fields.get("TotalTax"),
        "tip": document.fields.get("Tip"),
        "total": document.fields.get("Total")
    }

    simplified_receipt_data = simplify_receipt_data(receipt_data)
    return simplified_receipt_data

def callback(ch, method, properties, body):
    print(f" [x] Received {body}")
    
    # TODO: path, file, etc should be the payload of message, not 'hey'
    cmd = body.decode()

    if cmd == 'hey':
        receipt = get_s3_file(bucket=s3_config["bucket_name"], path='demo', file='kroger.jpg')
        data = analyze_receipt(receipt)
        
        ch.queue_declare(queue=amqp_config['processed_queue'], durable=True)
        ch.basic_publish(
            exchange='',
            routing_key=amqp_config['processed_queue'],
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,
            ))
    else:
        print("Unknown Body:")
        print(body)

    ch.basic_ack(delivery_tag=method.delivery_tag)


if __name__ == '__main__':
    connection, channel = connect_to_amqp(host=amqp_config['host'], port=amqp_config['port'], queue=[amqp_config['processed_queue'], amqp_config['unprocessed_queue']])
    print(' [OK] Waiting for messages...')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=amqp_config['unprocessed_queue'], on_message_callback=callback)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()
