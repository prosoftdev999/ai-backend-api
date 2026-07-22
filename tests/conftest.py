import os

os.environ.setdefault("APP_NAME", "AI Backend API Test")
os.environ.setdefault("APP_VERSION", "1.0.0")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("API_V1_PREFIX", "/api/v1")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/ai_backend",
)
os.environ.setdefault("REDIS_URL", "redis://redis:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://redis:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("EMBEDDING_MODEL", "test-embedding-model")
