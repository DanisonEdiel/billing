# Billing Domain Microservices

This repository contains four Python FastAPI microservices that handle the billing domain:

- **Tax Service**: Calculates taxes based on jurisdiction and product types
- **Discount Service**: Manages and applies discounts based on coupon codes, user types, and amount thresholds
- **Invoice Service**: Creates and manages invoices, including PDF generation
- **Payment Service**: Processes payments and communicates with payment gateways

## Architecture

### Hexagonal Architecture

Each microservice follows hexagonal architecture principles:
- **API Layer**: HTTP endpoints exposed via FastAPI
- **Service Layer**: Business logic and domain rules
- **Repository Layer**: Data access abstraction
- **Models**: Database entities using SQLAlchemy ORM
- **Schemas**: Data transfer objects using Pydantic

### Event-Driven Communication

Microservices communicate asynchronously via RabbitMQ:
- **Publishers**: Services publish domain events when state changes
- **Consumers**: Services subscribe to relevant events from other domains
- **Event Envelopes**: Standardized format for all events with metadata and payload

## Technologies

- **FastAPI**: Web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **aio-pika**: Asynchronous RabbitMQ client
- **JWT**: Authentication for API requests
- **Loguru**: Structured logging
- **Docker & Docker Compose**: Containerization and orchestration
- **PostgreSQL**: Relational database for each service
- **Alembic**: Database migrations

## Services

### Tax Service (Port 8001)
- Calculate tax rates based on jurisdiction
- Apply tax rules based on product categories
- Track tax calculation history

### Discount Service (Port 8002)
- Apply discounts based on coupon codes
- Apply user type discounts
- Apply amount-based threshold discounts
- Track discount application history

### Invoice Service (Port 8003)
- Create and manage invoices
- Generate PDF invoices
- Track invoice status and history
- Consume events from other services (tax calculations, discounts, payments)
- Calculate totals and apply taxes/discounts

### Payment Service (Port 8004)
- Process payments via payment gateways
- Track payment status and history
- Handle payment webhooks
- Publish payment events (received, failed)

## Setup & Deployment

### Prerequisites
- Docker and Docker Compose
- PostgreSQL (for local development without Docker)
- RabbitMQ (for local development without Docker)

### Environment Variables
Environment variables are stored in `.env` file at the root level and individual `.env` files in each service directory.

### Running with Docker Compose
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Running Locally (Development)
```bash
# Install dependencies in each service directory
cd tax-service
pip install -r requirements.txt

# Run migrations
cd migrations
alembic upgrade head

# Start service
uvicorn app.main:app --reload --port 8001

# Repeat for other services with their respective ports
```

## API Documentation
Once services are running, access Swagger UI docs at:
- Tax Service: http://localhost:8001/docs
- Discount Service: http://localhost:8002/docs
- Invoice Service: http://localhost:8003/docs
- Payment Service: http://localhost:8004/docs

## Database Migrations
Each service has its own Alembic setup for migrations:
```bash
cd <service-name>/migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Testing
Each service has unit and integration tests:
```bash
cd <service-name>
pytest
```

## Event Flow Examples

### Invoice Creation Flow
1. User creates an invoice via Invoice Service
2. Invoice Service requests tax calculation from Tax Service (HTTP)
3. Invoice Service requests discounts from Discount Service (HTTP)
4. Invoice Service publishes "invoice_created" event
5. Payment Service consumes "invoice_created" event to prepare for payment

### Payment Processing Flow
1. User initiates payment via Payment Service
2. Payment Service processes payment with gateway
3. Payment Service publishes "payment_received" event
4. Invoice Service consumes "payment_received" event and updates invoice status
