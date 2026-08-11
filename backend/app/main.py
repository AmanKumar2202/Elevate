"""
FastAPI application entry point with CORS, all routers, and lifespan-based seeding.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, users, feedback, hr


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    Startup: create SQLite tables (local dev) and auto-seed if empty.
    PostgreSQL users rely on 'alembic upgrade head' (see Dockerfile/README).
    """
    from app.db.session import SessionLocal, engine
    from app.models.models import Base
    from app.db.seed import seed_database
    from app.core.config import settings

    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    yield  # app runs here


app = FastAPI(
    title="Elevate — Performance Feedback API",
    description=(
        "Multi-tenant performance evaluation tool. "
        "Self-referencing manager hierarchy supports arbitrary org depth. "
        "All queries are company-scoped; company_id is always resolved server-side."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://frontend:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(hr.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}
