import pytest

from app import create_app
from app.extensions import db
from app.models import Category, User


@pytest.fixture()
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
            "SECRET_KEY": "test-secret",
        }
    )
    with app.app_context():
        db.create_all()
        users = [
            User(name="Gestor Teste", email="admin@test.com", role="admin"),
            User(name="Pessoa Teste", email="aluno@test.com", role="aluno"),
        ]
        for user in users:
            user.set_password("Senha123!")
        db.session.add_all(
            [
                Category(name="Elétrica", description="Instalações"),
                Category(name="Estrutura", description="Salas e portas"),
                *users,
            ]
        )
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def login(client):
    def do_login(email="aluno@test.com", password="Senha123!"):
        return client.post(
            "/auth/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

    return do_login
