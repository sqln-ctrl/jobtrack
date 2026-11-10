import os

from cryptography.fernet import Fernet

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.platforms import seed_default_platforms
from app.core.cookies import CSRF_COOKIE, SESSION_COOKIE
from app.core.security import create_session_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    seed_default_platforms(session)
    yield session
    session.close()


def make_user(db, n=1) -> User:
    user = User(google_id=f"g{n}", name=f"User {n}", email=f"user{n}@example.com")
    db.add(user)
    db.commit()
    return user


def make_client(db, user) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, create_session_token(user.id))
    client.cookies.set(CSRF_COOKIE, "csrf-test")
    client.headers["X-CSRF-Token"] = "csrf-test"
    return client


@pytest.fixture()
def user(db):
    return make_user(db)


@pytest.fixture()
def client(db, user):
    yield make_client(db, user)
    app.dependency_overrides.clear()
