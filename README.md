# receipt-worker

This project is a streamlined Python application that:

1. Subscribes to an AMQP queue for unprocessed receipts.
2. Downloads the corresponding receipt images from an S3-compatible bucket.
3. Utilizes Azure's Form Recognizer to extract relevant data from the downloaded images.
4. Publishes the processed data back to an AMQP queue.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

You will need to have the following installed:

- Python 3
- Access to an S3-compatible bucket
- An Azure account with Form Recognizer enabled
- A RabbitMQ server (or another AMQP server)

### Installing

Clone the repository to your local machine. Then install the required packages by running:

```bash
pip install -r requirements.txt
```

## Environment Variables

Variables without a default are required.

| Variable | Meaning | Default Value |
| --- | --- | --- |
| `AMQP_HOST` | The hostname of the AMQP server | 'rabbitmq' |
| `AMQP_PORT` | The port number of the AMQP server | '5672' |
| `AMQP_QUEUE_PREFIX` | The prefix for the names of the AMQP queues | 'receipts' |
| `S3_ACCESS_KEY_ID` | The access key ID for the S3 bucket |  |
| `S3_SECRET_ACCESS_KEY` | The secret access key for the S3 bucket |  |
| `S3_REGION` | The region where the S3 bucket is located | 'us-east-1' |
| `S3_BUCKET_NAME` | The name of the S3 bucket |  |
| `S3_ENDPOINT_URL` | The endpoint URL for the S3 service |  |
| `S3_PATH` | The path within the S3 bucket where the receipts are stored | 'receipts' |
| `AZURE_ENDPOINT_URL` | The endpoint URL for the Azure Form Recognizer service |  |
| `AZURE_KEY` | The key for the Azure Form Recognizer service |  |

## Running the Application

To run the application, use the following command:

```bash
python run.py
```

This will start the application and it will begin listening for messages on the AMQP queue.

## Processed Receipt Data

The processed queue is populated with receipt data that has been analyzed and formatted. The data is published to the queue as a JSON object.

### Structure of the Data

```json
{
  "receipt_type": "<type_of_receipt>",
  "merchant_name": {
    "value": "<name_of_merchant>",
    "confidence": <confidence_score>
  },
  "merchant_address": {
    "value": {
      "countryOrRegion": "<country_or_region>",
      "streetAddress": "<street_address>",
      "locality": "<locality>",
      "postalCode": "<postal_code>"
    },
    "confidence": <confidence_score>
  },
  "transaction_date": {
    "value": "<date_of_transaction>",
    "confidence": <confidence_score>
  },
  "items": [
    {
      "item_description": {
        "value": "<description_of_item>",
        "confidence": <confidence_score>
      },
      "item_quantity": {
        "value": <quantity_of_item>,
        "confidence": <confidence_score>
      },
      "item_price": {
        "value": <price_of_item>,
        "confidence": <confidence_score>
      },
      "item_total_price": {
        "value": <total_price_of_item>,
        "confidence": <confidence_score>
      }
    },
    ...
  ],
  "subtotal": {
    "value": <subtotal_amount>,
    "confidence": <confidence_score>
  },
  "tax": {
    "value": <tax_amount>,
    "confidence": <confidence_score>
  },
  "tip": {
    "value": <tip_amount>,
    "confidence": <confidence_score>
  },
  "total": {
    "value": <total_amount>,
    "confidence": <confidence_score>
  }
}
```

- `receipt_type`: The type of the receipt.
- `merchant_name`: The name of the merchant where the transaction took place.
- `merchant_address`: The address of the merchant. This is an object containing `countryOrRegion`, `streetAddress`, `locality`, and `postalCode`.
- `transaction_date`: The date when the transaction occurred.
- `items`: An array of items purchased. Each item is an object containing `item_description`, `item_quantity`, `item_price`, and `item_total_price`.
- `subtotal`: The subtotal amount of the transaction before tax and tip.
- `tax`: The amount of tax for the transaction.
- `tip`: The amount of tip for the transaction.
- `total`: The total amount of the transaction including tax and tip.

Each field (except `receipt_type` and `items`) is an object containing a `value` and a `confidence` score, which represents the confidence level of the data extraction process. In the `items` array, each field in an item is also an object with a `value` and a `confidence` score.


## License

This project is licensed under the MIT License.
