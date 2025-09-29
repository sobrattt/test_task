import time
from dotenv import load_dotenv
from connection import session
from api.database.models import Lead,LeadEvent
import pika
from pika.exceptions import AMQPConnectionError
import os


load_dotenv()

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT'))
RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE")


def callback(ch, method, properties, body):

    #decode abd get key
    lead_id = int(body.decode())
    lead = session.get(Lead, lead_id)

    if not lead:
        return f"lead {lead_id} not found"
    #updait company and status
    lead.company = "Unknown"
    lead.status = "enriched"

    #event create
    event = LeadEvent(event_type="enriched", lead_id=lead_id)

    session.add(event)
    session.commit()

def main():
    #connect to rabbitmq
    connection = None
    while not connection:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
        except AMQPConnectionError:
            time.sleep(5)

    channel = connection.channel()
    #queue check
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

    #start consuming
    channel.basic_consume(
        queue=RABBITMQ_QUEUE,
        on_message_callback=callback,
        auto_ack=True
    )

    channel.start_consuming()

if __name__ == "__main__":
    main()

