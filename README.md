# Lead Enrichment Service

This is a simple test project with a Flask API, a background worker, PostgreSQL, Redis, and RabbitMQ.  
The API accepts new leads, stores them in the database, and the worker enriches them asynchronously.

## 🚀 How to Run

1. Clone the repository:

git clone https://github.com/your-username/lead-service.git
cd lead-service

2. Make sure .env file is present in the root directory (it is included in the repo).
3. Start everything with Docker:
docker-compose up --build
 
The services will start:

API: http://localhost:5000

PostgreSQL, Redis, RabbitMQ — run inside Docker.

🧪 How to Test with Postman or curl

1️⃣ Create a Lead (POST)

Content-Type: application/json
idempotency-key: 123456789

Body (JSON):
{
  "email": "1234567@gmail.com",
  "phone": "333333",
  "name": "Andrew",
  "source": "qwerty"
}

✅ Expected response:
{
  "lead id": 1
}

2️⃣ Get Lead by ID (GET)

http://localhost:5000/leads/1

✅ Expected response after the worker processes the message:

{
  "id": 1,
  "email": "1234567@gmail.com",
  "phone": "333333",
  "name": "Andrew",
  "source": "qwerty",
  "company": "Unknown",
  "status": "enriched"
}

📝 Notes

Make sure Docker is running before starting the services.

The first request creates a new lead and sends its ID to RabbitMQ.

The worker picks it up, enriches it, and updates the database.

The second request returns the enriched lead data.

I didn't have time to implement migrations, it took around 10 hours.

