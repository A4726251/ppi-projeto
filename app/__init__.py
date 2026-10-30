import os
from pathlib import Path

import click
from flask import Flask

from app.extensions import csrf, db, login_manager


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    instance_dir = Path(app.instance_path)
    default_upload_dir = Path(app.root_path) / "static" / "uploads"
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{(instance_dir / 'ifcm.db').as_posix()}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.environ.get("UPLOAD_FOLDER", str(default_upload_dir)),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app import models  # noqa: F401
    from app.admin import admin_bp
    from app.auth import auth_bp
    from app.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    @app.cli.command("seed-demo")
    def seed_demo():
        """Create local demonstration accounts and starter categories."""
        from app.models import Category, User

        if not User.query.filter_by(email="admin@ifcm.edu.br").first():
            admin = User(name="Gestor IFCM", email="admin@ifcm.edu.br", role="admin")
            admin.set_password("Admin123!")
            db.session.add(admin)
        if not User.query.filter_by(email="aluno@ifcm.edu.br").first():
            student = User(name="Estudante de demonstração", email="aluno@ifcm.edu.br", role="aluno")
            student.set_password("Aluno123!")
            db.session.add(student)

        starter_categories = [
            ("Elétrica", "Lâmpadas, tomadas e instalações elétricas."),
            ("Hidráulica", "Vazamentos, torneiras e instalações hidráulicas."),
            ("Estrutura", "Portas, janelas, fechaduras, salas e áreas comuns."),
            ("Equipamentos", "Computadores, ventiladores e outros equipamentos."),
            ("Limpeza e conservação", "Banheiros, pátios e conservação dos espaços."),
        ]
        for name, description in starter_categories:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name, description=description))

        db.session.commit()
        click.echo("Dados de demonstração criados (ou já existentes).")

    @app.cli.command("init-db")
    def init_db():
        """Create database tables."""
        db.create_all()
        click.echo("Banco de dados inicializado.")

    return app
