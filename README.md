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

The following table lists the environment variables used by this application, their meanings, and default values if applicable.

| Variable | Meaning | Default Value |
| --- | --- | --- |
| `AMQP_HOST` | The hostname of the AMQP server | 'rabbitmq' |
| `AMQP_PORT` | The port number of the AMQP server | '5672' |
| `AMQP_QUEUE_PREFIX` | The prefix for the names of the AMQP queues | 'receipts' |
| `S3_ACCESS_KEY_ID` | The access key ID for the S3 bucket | N/A |
| `S3_SECRET_ACCESS_KEY` | The secret access key for the S3 bucket | N/A |
| `S3_REGION` | The region where the S3 bucket is located | 'us-east-1' |
| `S3_BUCKET_NAME` | The name of the S3 bucket | N/A |
| `S3_ENDPOINT_URL` | The endpoint URL for the S3 service | N/A |
| `S3_PATH` | The path within the S3 bucket where the receipts are stored | 'receipts' |
| `AZURE_ENDPOINT_URL` | The endpoint URL for the Azure Form Recognizer service | N/A |
| `AZURE_KEY` | The key for the Azure Form Recognizer service | N/A |

## Running the Application

To run the application, use the following command:

```bash
python run.py
```

This will start the application and it will begin listening for messages on the AMQP queue.

## License

This project is licensed under the MIT License.
