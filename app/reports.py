from pathlib import Path
from uuid import uuid4

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms import ReportForm
from app.models import Category, Report, ReportHistory

reports_bp = Blueprint("reports", __name__)
STATUSES = ("Aberto", "Em análise", "Em andamento", "Resolvido", "Arquivado")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}


@reports_bp.get("/")
def home():
    return redirect(url_for("reports.list_reports") if current_user.is_authenticated else url_for("auth.login"))


@reports_bp.get("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@reports_bp.route("/solicitacoes", methods=["GET", "POST"])
@login_required
def list_reports():
    query = Report.query.join(Category)
    category_id = request.args.get("categoria", type=int)
    status = request.args.get("status", "")
    location = request.args.get("local", "").strip()
    if category_id:
        query = query.filter(Report.category_id == category_id)
    if status in STATUSES:
        query = query.filter(Report.status == status)
    if location:
        query = query.filter(Report.location.ilike(f"%{location}%"))

    reports = query.order_by(Report.created_at.desc()).all()
    categories = Category.query.filter_by(active=True).order_by(Category.name).all()
    return render_template(
        "reports/list.html",
        reports=reports,
        categories=categories,
        selected_category=category_id,
        selected_status=status if status in STATUSES else "",
        selected_location=location,
        statuses=STATUSES,
    )


@reports_bp.route("/solicitacoes/nova", methods=["GET", "POST"])
@login_required
def create_report():
    form = ReportForm()
    categories = Category.query.filter_by(active=True).order_by(Category.name).all()
    form.category_id.choices = [(category.id, category.name) for category in categories]
    if not categories:
        flash("Ainda não há categorias disponíveis. Peça a um gestor para cadastrar uma.", "warning")
        return redirect(url_for("reports.list_reports"))

    if form.validate_on_submit():
        category = db.session.get(Category, form.category_id.data)
        if category is None or not category.active:
            form.category_id.errors.append("Selecione uma categoria ativa.")
            return render_template("reports/new.html", form=form)

        image_filename = None
        image = form.image.data
        if image and image.filename:
            original_name = secure_filename(image.filename)
            extension = Path(original_name).suffix.lower().lstrip(".")
            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                form.image.errors.append("Envie uma imagem JPG, PNG, GIF ou WEBP.")
                return render_template("reports/new.html", form=form)
            image_filename = f"{uuid4().hex}.{extension}"
            image.save(Path(current_app.config["UPLOAD_FOLDER"]) / image_filename)

        report = Report(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            location=form.location.data.strip(),
            category=category,
            author=current_user,
            image_filename=image_filename,
        )
        report.history.append(
            ReportHistory(actor=current_user, status="Aberto", note="Solicitação registrada.")
        )
        db.session.add(report)
        db.session.commit()
        flash("Problema registrado com sucesso.", "success")
        return redirect(url_for("reports.report_detail", report_id=report.id))

    if "Not a valid choice." in form.category_id.errors:
        form.category_id.errors = ["Selecione uma categoria ativa."]
    return render_template("reports/new.html", form=form)


@reports_bp.get("/solicitacoes/<int:report_id>")
@login_required
def report_detail(report_id):
    report = db.session.get(Report, report_id)
    if report is None:
        abort(404)
    update_form = None
    if current_user.is_admin:
        from app.forms import ReportUpdateForm

        update_form = ReportUpdateForm(status=report.status, priority=report.priority)
    return render_template("reports/detail.html", report=report, update_form=update_form)


@reports_bp.post("/solicitacoes/<int:report_id>/atualizar")
@login_required
def update_report(report_id):
    if not current_user.is_admin:
        abort(403)
    report = db.session.get(Report, report_id)
    if report is None:
        abort(404)

    from app.forms import ReportUpdateForm

    form = ReportUpdateForm()
    if form.validate_on_submit():
        changed = report.status != form.status.data or report.priority != form.priority.data
        report.status = form.status.data
        report.priority = form.priority.data
        note = form.note.data.strip() if form.note.data else ""
        if changed or note:
            report.history.append(
                ReportHistory(actor=current_user, status=report.status, note=note)
            )
        db.session.commit()
        flash("Solicitação atualizada.", "success")
    else:
        flash("Não foi possível atualizar. Confira os campos informados.", "danger")
    return redirect(url_for("reports.report_detail", report_id=report.id))
