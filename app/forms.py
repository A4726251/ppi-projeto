from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


def strip_string(value):
    return value.strip() if isinstance(value, str) else value


class RegistrationForm(FlaskForm):
    name = StringField("Nome", filters=[strip_string], validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("E-mail", filters=[strip_string], validators=[DataRequired(), Email(), Length(max=254)])
    role = SelectField(
        "Perfil",
        choices=[("aluno", "Aluno"), ("professor", "Professor"), ("funcionario", "Funcionário")],
        validators=[DataRequired()],
    )
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirme a senha",
        validators=[DataRequired(), EqualTo("password", message="As senhas não conferem.")],
    )
    submit = SubmitField("Criar conta")


class LoginForm(FlaskForm):
    email = StringField("E-mail", filters=[strip_string], validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField("Senha", validators=[DataRequired()])
    remember = BooleanField("Manter conectado")
    submit = SubmitField("Entrar")


class ReportForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired(), Length(min=4, max=120)])
    description = TextAreaField("Descrição", validators=[DataRequired(), Length(min=10, max=4000)])
    category_id = SelectField("Categoria", coerce=int, validators=[DataRequired()])
    location = StringField("Local", validators=[DataRequired(), Length(min=2, max=120)])
    image = FileField(
        "Foto (opcional)",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif", "webp"], "Envie uma imagem JPG, PNG, GIF ou WEBP.")],
    )
    submit = SubmitField("Registrar problema")


class ReportUpdateForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[
            ("Aberto", "Aberto"),
            ("Em análise", "Em análise"),
            ("Em andamento", "Em andamento"),
            ("Resolvido", "Resolvido"),
            ("Arquivado", "Arquivado"),
        ],
        validators=[DataRequired()],
    )
    priority = SelectField(
        "Prioridade",
        choices=[("Baixa", "Baixa"), ("Normal", "Normal"), ("Alta", "Alta"), ("Urgente", "Urgente")],
        validators=[DataRequired()],
    )
    note = TextAreaField("Observação", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Atualizar solicitação")


class CategoryForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(min=2, max=60)])
    description = TextAreaField("Descrição", validators=[Optional(), Length(max=250)])
    active = BooleanField("Categoria ativa", default=True)
    submit = SubmitField("Salvar categoria")
