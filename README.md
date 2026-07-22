# AI Backend API

A production-ready AI backend built with **FastAPI**, **PostgreSQL + pgvector**, **Redis**, **Celery**, and the **OpenAI API**.

The project provides document upload, background processing, vector embeddings, semantic search, Retrieval-Augmented Generation (RAG), and chat session management.

---

## Features

- FastAPI REST API
- PostgreSQL + pgvector
- Redis
- Celery background workers
- Flower monitoring
- Alembic database migrations
- OpenAI Embeddings
- OpenAI Chat Completion
- Semantic Vector Search
- Retrieval-Augmented Generation (RAG)
- Document Upload API
- Automatic document chunking
- Async SQLAlchemy
- Docker Compose
- Pytest

---

# Architecture

```
                +----------------+
                |    FastAPI     |
                +--------+-------+
                         |
                         |
              Upload / Chat API
                         |
                         v
                PostgreSQL Database
                  + pgvector
                         |
                         |
          +--------------+--------------+
          |                             |
          |                             |
          v                             v
      Celery Worker                 Search API
          |                             |
          |                             |
          v                             |
   Document Processing                  |
          |                             |
          v                             |
    OpenAI Embeddings ------------------+
          |
          v
      Vector Storage

```

---

# Tech Stack

| Technology | Purpose |
|------------|---------|
| FastAPI | REST API |
| PostgreSQL | Database |
| pgvector | Vector Database |
| SQLAlchemy | ORM |
| Alembic | Database Migration |
| Redis | Message Broker |
| Celery | Background Jobs |
| Flower | Celery Dashboard |
| Docker | Containers |
| OpenAI API | Embeddings & Chat |
| PyPDF | PDF Parsing |
| python-docx | DOCX Parsing |
| Pytest | Testing |

---

# Project Structure

```
app/
│
├── api/
│   └── routes/
│
├── core/
│
├── db/
│
├── models/
│
├── schemas/
│
├── services/
│
├── tasks/
│
├── utils/
│
└── main.py

alembic/

tests/

docker-compose.yml

requirements.txt
```

---

# Installation

Clone repository

```bash
git clone git@github.com:prosoftdev999/ai-backend-api.git

cd ai-backend-api
```

---

## Create Environment

```bash
python -m venv .venv

source .venv/bin/activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# Configure Environment

Create `.env`

Example

```env
APP_NAME=AI Backend API

DEBUG=true

DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/ai_backend

REDIS_URL=redis://redis:6379/0

OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx

OPENAI_CHAT_MODEL=gpt-5.5

OPENAI_EMBEDDING_MODEL=text-embedding-3-small

VECTOR_DIMENSIONS=1536
```

---

# Start Docker

```bash
docker compose up --build
```

Services

| Service | Port |
|---------|------|
| FastAPI | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Flower | 5555 |

---

# Database Migration

Create migration

```bash
docker compose run --rm api alembic revision --autogenerate -m "Initial"
```

Apply migration

```bash
docker compose run --rm api alembic upgrade head
```

---

# API Documentation

Swagger

```
http://localhost:8000/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

# Flower Dashboard

```
http://localhost:5555
```

---

# Running Tests

```bash
pytest
```

or

```bash
docker compose run --rm api pytest
```

---

# Example API

## Upload Document

```http
POST /api/v1/documents
```

Form Data

```
file=@sample.pdf
```

---

## Search

```http
POST /api/v1/search
```

Example

```json
{
    "query":"What is FastAPI?",
    "limit":5
}
```

---

## Create Chat Session

```http
POST /api/v1/chat/sessions
```

Example

```json
{
    "title":"AI Chat"
}
```

---

## Send Chat Message

```http
POST /api/v1/chat/sessions/{session_id}/messages
```

Example

```json
{
    "content":"Explain FastAPI."
}
```

---

# Development

Run API

```bash
uvicorn app.main:app --reload
```

Run Worker

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

Run Flower

```bash
celery -A app.tasks.celery_app flower
```

---

# Environment Variables

| Variable | Description |
|----------|-------------|
| OPENAI_API_KEY | OpenAI API Key |
| DATABASE_URL | PostgreSQL URL |
| REDIS_URL | Redis URL |
| OPENAI_CHAT_MODEL | Chat Model |
| OPENAI_EMBEDDING_MODEL | Embedding Model |
| VECTOR_DIMENSIONS | Embedding Dimension |

---

# Current Status

- ✅ FastAPI
- ✅ PostgreSQL
- ✅ pgvector
- ✅ Docker
- ✅ Redis
- ✅ Celery
- ✅ Flower
- ✅ Alembic
- ✅ Document Upload
- ✅ Background Processing
- ✅ OpenAI Embeddings
- ✅ Vector Search
- ✅ RAG
- ✅ Chat Sessions
- ✅ REST API
- ✅ Docker Compose
- ✅ Unit Tests

---

# License

MIT License

---

# Author

**Johan Bergman**

GitHub

https://github.com/prosoftdev999

---

# Repository

https://github.com/prosoftdev999/ai-backend-api