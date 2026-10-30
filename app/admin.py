from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.forms import CategoryForm
from app.models import Category, Report, User

admin_bp = Blueprint("admin", __name__, url_prefix="/gestao")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@admin_bp.get("/")
@admin_required
def dashboard():
    return render_template(
        "admin/dashboard.html",
        total_reports=Report.query.count(),
        open_reports=Report.query.filter(Report.status != "Resolvido", Report.status != "Arquivado").count(),
        total_users=User.query.count(),
        categories=Category.query.order_by(Category.name).all(),
        recent_reports=Report.query.order_by(Report.created_at.desc()).limit(8).all(),
    )


@admin_bp.route("/categorias/nova", methods=["GET", "POST"])
@admin_required
def create_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data.strip(),
            description=(form.description.data or "").strip(),
            active=form.active.data,
        )
        db.session.add(category)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.name.errors.append("Já existe uma categoria com esse nome.")
        else:
            flash("Categoria cadastrada.", "success")
            return redirect(url_for("admin.dashboard"))
    return render_template("admin/category_form.html", form=form, heading="Nova categoria")


@admin_bp.route("/categorias/<int:category_id>/editar", methods=["GET", "POST"])
@admin_required
def edit_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        abort(404)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        category.name = form.name.data.strip()
        category.description = (form.description.data or "").strip()
        category.active = form.active.data
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.name.errors.append("Já existe uma categoria com esse nome.")
        else:
            flash("Categoria atualizada.", "success")
            return redirect(url_for("admin.dashboard"))
    return render_template("admin/category_form.html", form=form, heading="Editar categoria")
