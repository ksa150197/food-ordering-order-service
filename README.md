# Food Ordering System – Order Service

A RESTful microservice responsible for creating and managing customer orders in the Food Ordering and Management System. Developed using **Python FastAPI**, **SQLAlchemy**, **Pydantic**, and **HTTPX**.

## 1. Project Overview

The Order Service manages customer orders and coordinates with the Menu Service to validate food items before accepting an order.

When a customer submits an order, the Order Service communicates with the Menu Service using synchronous REST/HTTP communication. It retrieves the requested food item details, validates their availability, obtains their current prices, calculates the order total, and stores the order in its own database.

The Order Service maintains independent data ownership and does not directly access the Menu Service database.

## 2. Key Features

- Create customer orders containing multiple food items.
- Validate food item IDs through the Menu Service.
- Verify food item availability before accepting orders.
- Retrieve current food item prices from the Menu Service.
- Calculate order totals based on item prices and quantities.
- Maintain item name and price snapshots within orders.
- Retrieve all orders.
- Retrieve orders using an order ID.
- Filter orders using customer ID.
- Update order status.
- Cancel eligible orders.
- Health-check endpoint for service monitoring.
- Automatic API documentation through FastAPI Swagger UI.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Programming language |
| FastAPI 0.115.12 | REST API framework |
| SQLAlchemy 2.0.40 | Database ORM |
| Pydantic 2.11.3 | Request and response validation |
| HTTPX 0.28.1 | REST communication with Menu Service |
| PostgreSQL | Persistent database |
| SQLite | Local development fallback |
| Docker | Containerisation |
| Uvicorn 0.34.0 | ASGI application server |

## 4. Project Structure

```text
order-service/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── database.py
│
├── Dockerfile
├── requirements.txt
└── README.md
```

### Application Components

- **main.py:** Implements order creation, retrieval, status updates, cancellation, and communication with Menu Service.
- **models.py:** Defines the SQLAlchemy database model for customer orders.
- **schemas.py:** Defines Pydantic models for order requests, responses, and status updates.
- **database.py:** Configures the database connection and SQLAlchemy sessions.
- **Dockerfile:** Defines how the Order Service container image is built.

## 5. Architecture and Service Communication

The Order Service communicates with the Menu Service through synchronous REST/HTTP requests.

The order creation workflow is:

1. Customer submits an order request to the Order Service.
2. Order Service receives the requested item IDs and quantities.
3. Order Service sends HTTP GET requests to the Menu Service for each requested item.
4. Menu Service returns the food item details, including name, price, and availability.
5. Order Service validates the returned information.
6. Order Service calculates the total order amount.
7. Order Service stores the order and item-price snapshots in its own database.
8. Order confirmation is returned to the customer.

If a food item does not exist or is unavailable, the order is rejected.

If the Menu Service is unavailable or returns an invalid response, order creation fails with an HTTP 503 response.

### Service Communication URL

The Menu Service URL is configurable using the `MENU_SERVICE_URL` environment variable.

Default local configuration:

```text
http://localhost:8000
```

Kubernetes configuration:

```text
http://menu-service:8000
```

## 6. Database Design

The Order Service maintains its own PostgreSQL database named `order_db`.

The order records contain:

| Attribute | Description |
|---|---|
| id | Unique order identifier |
| customer_id | Customer identifier |
| items | Ordered item details stored as snapshots |
| total_amount | Calculated order amount |
| status | Current order status |
| created_at | Order creation timestamp |

Each item snapshot contains:

- Item ID.
- Item name.
- Unit price.
- Quantity.
- Line total.

Maintaining item and price snapshots ensures that historical orders retain the prices that were used when they were created, even if menu prices subsequently change.

## 7. API Endpoints

The service exposes the following REST APIs:

| HTTP Method | Endpoint | Description |
|---|---|---|
| POST | `/orders` | Create a new order |
| GET | `/orders` | Retrieve all orders |
| GET | `/orders?customer_id=CUST-1001` | Retrieve orders for a customer |
| GET | `/orders/{order_id}` | Retrieve an individual order |
| PATCH | `/orders/{order_id}/status` | Update order status |
| PATCH | `/orders/{order_id}/cancel` | Cancel an eligible order |
| GET | `/health` | Check service health |

### Supported Order Statuses

The service supports the following statuses:

- PLACED
- CONFIRMED
- PREPARING
- READY
- COMPLETED
- CANCELLED

Only orders in `PLACED` or `CONFIRMED` status can be cancelled.

Completed or cancelled orders cannot be updated through the status endpoint.

## 8. Example: Create an Order

**Request**

```http
POST /orders
Content-Type: application/json
```

```json
{
  "customer_id": "CUST-1001",
  "items": [
    {
      "item_id": 1,
      "quantity": 2
    }
  ]
}
```

The Order Service retrieves the food item information from the Menu Service before creating the order.

**Expected response:** `201 Created`

```json
{
  "id": 1,
  "customer_id": "CUST-1001",
  "items": [
    {
      "item_id": 1,
      "name": "Paneer Wrap",
      "unit_price": "149.0",
      "quantity": 2,
      "line_total": "298.0"
    }
  ],
  "total_amount": 298.0,
  "status": "PLACED",
  "created_at": "2026-11-12T10:00:00"
}
```

The order ID and timestamp are generated by the application.

## 9. Local Setup and Execution

### Prerequisites

- Python 3.12 or later.
- pip package manager.
- Git.
- Menu Service running and accessible.

### Step 1: Clone the repository

```bash
git clone https://github.com/ksa150197/food-ordering-order-service.git
cd food-ordering-order-service
```

### Step 2: Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables

Configure the Menu Service URL:

```bash
export MENU_SERVICE_URL="http://localhost:8000"
```

For PostgreSQL, configure the database connection:

```bash
export DATABASE_URL="postgresql+psycopg://fooduser:foodpass@localhost:5432/order_db"
```

If `DATABASE_URL` is not configured, the service uses a local SQLite database named `orders.db`.

### Step 5: Start the service

```bash
uvicorn app.main:app --reload --port 8001
```

Access the API documentation:

http://localhost:8001/docs

**Important:** The Menu Service must be running and accessible at the configured URL for successful order creation.

## 10. Docker Deployment

Build the Docker image from the repository root:

```bash
docker build -t food-order-service:latest .
```

Run the container:

```bash
docker run -d \
  --name order-service \
  -p 8001:8001 \
  -e DATABASE_URL="postgresql+psycopg://fooduser:foodpass@host.docker.internal:5432/order_db" \
  -e MENU_SERVICE_URL="http://host.docker.internal:8000" \
  food-order-service:latest
```

The PostgreSQL server and Menu Service must be reachable using the configured addresses.

Verify the container:

```bash
docker ps
```

Access Swagger UI:

http://localhost:8001/docs

## 11. Kubernetes Deployment

The Order Service was deployed to a local Kubernetes cluster using Minikube.

The Kubernetes configuration includes:

- A Kubernetes Deployment with one replica.
- A Kubernetes Service for network access.
- A container image named `food-order-service:latest`.
- A PostgreSQL database connection.
- A Menu Service URL configured through Kubernetes DNS.
- A readiness probe using the `/health` endpoint.

The service communicates with the Menu Service internally through:

```text
http://menu-service:8000
```

The Kubernetes manifests are maintained separately in the main project deployment directory.

## 12. Health Check

The service exposes:

```http
GET /health
```

Example response:

```json
{
  "service": "order-service",
  "status": "healthy"
}
```

This endpoint is also used by the Kubernetes readiness probe.

## 13. Repository

GitHub: https://github.com/ksa150197/food-ordering-order-service

## 14. Project Scope

This microservice was developed as part of an individual Scalable Services assignment to demonstrate:

- Independent microservice development.
- REST-based inter-service communication.
- Database ownership and persistence.
- Order validation and processing.
- Docker containerisation.
- Kubernetes deployment using Minikube.

This is an academic demonstration project and is not intended as a production-hardened application.