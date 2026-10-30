from io import BytesIO
from pathlib import Path

from app.extensions import db
from app.models import Category, Report, ReportHistory, User


def create_report(client, category_id=1, **overrides):
    data = {
        "title": "Lâmpada queimada",
        "description": "A lâmpada da sala está queimada e precisa de substituição.",
        "category_id": str(category_id),
        "location": "Bloco A, sala 12",
    }
    data.update(overrides)
    return client.post("/solicitacoes/nova", data=data, follow_redirects=True)


def test_home_redirects_anonymous_user_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_login_page_is_available(client):
    assert client.get("/auth/login").status_code == 200


def test_registration_creates_user_with_password_hash(app, client):
    response = client.post(
        "/auth/cadastro",
        data={
            "name": "Nova Pessoa",
            "email": " NOVO@EXAMPLE.COM ",
            "role": "aluno",
            "password": "SenhaForte123",
            "confirm_password": "SenhaForte123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="novo@example.com").one()
        assert user.check_password("SenhaForte123")
        assert user.password_hash != "SenhaForte123"


def test_registration_rejects_mismatched_passwords(client):
    response = client.post(
        "/auth/cadastro",
        data={
            "name": "Nova Pessoa",
            "email": "novo@example.com",
            "role": "aluno",
            "password": "SenhaForte123",
            "confirm_password": "SenhaDiferente123",
        },
    )
    assert response.status_code == 200
    assert "As senhas não conferem" in response.get_data(as_text=True)


def test_registration_rejects_duplicate_email(client):
    response = client.post(
        "/auth/cadastro",
        data={
            "name": "Outra Pessoa",
            "email": "ALUNO@test.com",
            "role": "aluno",
            "password": "SenhaForte123",
            "confirm_password": "SenhaForte123",
        },
    )
    assert response.status_code == 200
    assert "já está cadastrado" in response.get_data(as_text=True)


def test_login_accepts_valid_credentials(client, login):
    response = login()
    assert response.status_code == 200
    assert "Problemas da escola" in response.get_data(as_text=True)


def test_login_rejects_invalid_password(client):
    response = client.post(
        "/auth/login",
        data={"email": "aluno@test.com", "password": "incorreta"},
        follow_redirects=True,
    )
    assert "E-mail ou senha inválidos" in response.get_data(as_text=True)


def test_logout_ends_session(client, login):
    login()
    response = client.post("/auth/logout", follow_redirects=True)
    assert "Você saiu da sua conta" in response.get_data(as_text=True)
    assert "Entrar" in response.get_data(as_text=True)


def test_report_list_requires_authentication(client):
    assert client.get("/solicitacoes").status_code == 302


def test_new_report_page_requires_authentication(client):
    assert client.get("/solicitacoes/nova").status_code == 302


def test_authenticated_user_can_open_report_form(client, login):
    login()
    response = client.get("/solicitacoes/nova")
    assert response.status_code == 200
    assert "Registrar problema" in response.get_data(as_text=True)


def test_report_creation_persists_report_and_initial_history(app, client, login):
    login()
    response = create_report(client)
    assert response.status_code == 200
    with app.app_context():
        report = Report.query.one()
        assert report.title == "Lâmpada queimada"
        assert report.author.email == "aluno@test.com"
        assert report.category.name == "Elétrica"
        assert report.status == "Aberto"
        assert report.history[0].note == "Solicitação registrada."


def test_report_form_rejects_invalid_fields(client, login):
    login()
    response = create_report(
        client,
        title="x",
        description="curta",
        location="",
    )
    assert response.status_code == 200
    assert "Field must be between" in response.get_data(as_text=True)


def test_report_creation_accepts_photo(app, client, login):
    login()
    response = client.post(
        "/solicitacoes/nova",
        data={
            "title": "Computador sem imagem",
            "description": "O computador da biblioteca liga mas não apresenta imagem.",
            "category_id": "2",
            "location": "Biblioteca",
            "image": (BytesIO(b"fake image data"), "foto.png"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        report = Report.query.one()
        assert report.image_filename.endswith(".png")
        assert (Path(app.config["UPLOAD_FOLDER"]) / report.image_filename).is_file()


def test_report_filters_by_category_status_and_location(client, login):
    login()
    create_report(client, category_id=1)
    create_report(
        client,
        category_id=2,
        title="Porta quebrada",
        description="A porta da sala está com a fechadura quebrada.",
        location="Bloco B, sala 3",
    )
    response = client.get("/solicitacoes?categoria=2&status=Aberto&local=Bloco+B")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Porta quebrada" in page
    assert "Lâmpada queimada" not in page


def test_report_detail_returns_not_found_for_missing_report(client, login):
    login()
    assert client.get("/solicitacoes/999").status_code == 404


def test_regular_user_cannot_access_admin_dashboard(client, login):
    login()
    assert client.get("/gestao/").status_code == 403


def test_admin_can_update_report_and_create_history(app, client):
    client.post("/auth/login", data={"email": "aluno@test.com", "password": "Senha123!"})
    client.post(
        "/solicitacoes/nova",
        data={
            "title": "Lâmpada queimada",
            "description": "A lâmpada da sala está queimada e precisa de substituição.",
            "category_id": "1",
            "location": "Bloco A, sala 12",
        },
    )
    client.post("/auth/logout")
    client.post("/auth/login", data={"email": "admin@test.com", "password": "Senha123!"})
    response = client.post(
        "/solicitacoes/1/atualizar",
        data={"status": "Em andamento", "priority": "Alta", "note": "Equipe acionada."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        report = db.session.get(Report, 1)
        assert report.status == "Em andamento"
        assert report.priority == "Alta"
        assert report.history[-1].note == "Equipe acionada."


def test_admin_can_create_category(app, client):
    client.post("/auth/login", data={"email": "admin@test.com", "password": "Senha123!"})
    response = client.post(
        "/gestao/categorias/nova",
        data={"name": "Mobiliário", "description": "Mesas e cadeiras", "active": "y"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Category.query.filter_by(name="Mobiliário", active=True).one()


def test_regular_user_cannot_create_category(client, login):
    login()
    assert client.get("/gestao/categorias/nova").status_code == 403


def test_admin_can_deactivate_category(app, client):
    client.post("/auth/login", data={"email": "admin@test.com", "password": "Senha123!"})
    response = client.post(
        "/gestao/categorias/1/editar",
        data={"name": "Elétrica", "description": "Instalações", "active": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Category, 1).active is False


def test_new_report_rejects_inactive_category(app, client, login):
    with app.app_context():
        db.session.get(Category, 1).active = False
        db.session.commit()
    login()
    response = create_report(client, category_id=1)
    assert "Selecione uma categoria ativa" in response.get_data(as_text=True)
