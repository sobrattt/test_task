import json
import time
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from api.database.models import Lead
from api.database.connection import session
import re
import redis
import pika
import os


blueprint = Blueprint("api", __name__)

load_dotenv()

RATE_LIMIT = int(os.environ.get("RATE_LIMIT"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW"))
EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT"))
REDIS_DB = int(os.environ.get("REDIS_DB"))

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT'))
RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE")

IDEMPOTENCY_KEY_TIME = int(os.environ.get("IDEMPOTENCY_KEY_TIME"))


redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def get_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    return channel


@blueprint.post("/lead")
def lead_handle():
    data = request.get_json()
    key = request.headers.get("idempotency-key")
    ip = request.remote_addr

    # Request must have idempotency key
    if not key:
        return jsonify({"error": "idempotency-key not exists"}) , 400

    # Validate email
    email = data.get("email")
    if not re.match(EMAIL_REGEX, email):
        return jsonify({"error": "invalid email format"}), 400

    # Rate limiting
    current_time = int(time.time())
    key_ip = f"ratelimit:{ip}:{current_time // RATE_LIMIT_WINDOW}"
    request_count = redis_client.incr(key_ip)
    if request_count == 1:
        redis_client.expire(key_ip, RATE_LIMIT_WINDOW)
    if request_count > RATE_LIMIT:
        return jsonify({"error": "To many requests"}), 400

    #check email existing
    existing_email = session.query(Lead).filter_by(email=email).first()
    if existing_email:
        return jsonify({"error": "Email already exists"}), 400

    # save new lead
    lead = Lead(
        email = email,
        phone = data.get("phone"),
        name = data.get("name"),
        source = data.get("source"),
        # status = "new"
    )
    session.add(lead)
    session.commit()

    #sending the lead id to rabbitmq
    channel = get_rabbitmq()
    channel.basic_publish(
        exchange="",
        routing_key=RABBITMQ_QUEUE,
        body=str(lead.id)
    )
    channel.close()

    #marking idempotency key as used
    redis_client.setex(f"Idempotency:{key}", IDEMPOTENCY_KEY_TIME, "used")
    return jsonify({"lead id": lead.id}), 200

@blueprint.get("/leads/<lead_id>")
def get_lead_by_id_handle(lead_id):
    cache_key = f"lead:{lead_id}"

    #getting lead from redis
    key_exist = redis_client.get(cache_key)
    if key_exist:
        return jsonify(json.loads(key_exist)), 200

    #getting lead from db
    lead = session.get(Lead, lead_id)
    if not lead:
        return jsonify({"error": "not found"}), 400

    #lead to dict
    lead_data = {
        "id" : lead_id,
        "email" : lead.email,
        "phone" : lead.phone,
        "name" : lead.name,
        "source": lead.source,
        "status": lead.status,
        "company": lead.company
    }
    #save in redis cache
    redis_client.setex(cache_key, 60, json.dumps(lead_data))

    return jsonify(lead_data), 200


