import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from app.extensions import db
from app.models import AdminPDF, UserPDF
from .forms import PDFUploadForm
from werkzeug.utils import safe_join

bp = Blueprint("library", __name__, template_folder='../../templates/library')


@bp.route("/")
def index():
    # Choose where to redirect
    if current_user.is_authenticated:
        return redirect(url_for("library.user_library"))
    return redirect(url_for("library.readings"))


@bp.route("/readings")
def readings():
    pdfs = AdminPDF.query.order_by(AdminPDF.uploaded_at.desc()).all()
    return render_template("library/readings.html", pdfs=pdfs)


@bp.route("/readings/upload", methods=["GET", "POST"])
@login_required
def upload_reading():
    if not current_user.is_admin:
        flash("Only admins can upload to Readings.", "danger")
        return redirect(url_for("library.readings"))

    form = PDFUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = file.filename

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        path = os.path.join(upload_folder, filename)
        file.save(path)

        pdf = AdminPDF(title=form.title.data, description=form.description.data, filename=filename)
        db.session.add(pdf)
        db.session.commit()

        flash("PDF uploaded successfully!", "success")
        return redirect(url_for("library.readings"))

    return render_template("library/upload.html", form=form, heading="Upload Reading (Admin)")


@bp.route("/user")
def user_library():
    pdfs = UserPDF.query.order_by(UserPDF.uploaded_at.desc()).all()
    return render_template("library/user_library.html", pdfs=pdfs)


@bp.route("/user/upload", methods=["GET", "POST"])
@login_required
def upload_user_pdf():
    form = PDFUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = file.filename

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        path = os.path.join(upload_folder, filename)
        file.save(path)

        pdf = UserPDF(user_id=current_user.id, title=form.title.data, description=form.description.data, filename=filename)
        db.session.add(pdf)
        db.session.commit()

        flash("Your PDF was uploaded!", "success")
        return redirect(url_for("library.user_library"))

    return render_template("library/upload.html", form=form, heading="Upload to My Library")


@bp.route("/delete/<string:kind>/<int:pdf_id>")
@login_required
def delete_pdf(kind, pdf_id):
    if kind == "admin":
        pdf = AdminPDF.query.get_or_404(pdf_id)
        if not current_user.is_admin:
            flash("Only admins can delete admin PDFs.", "danger")
            return redirect(url_for("library.readings"))

        db.session.delete(pdf)
        db.session.commit()
        flash("Admin PDF deleted.", "info")
        return redirect(url_for("library.readings"))

    elif kind == "user":
        pdf = UserPDF.query.get_or_404(pdf_id)
        if current_user.id != pdf.user_id and not current_user.is_admin:
            flash("You don't have permission to delete this file.", "danger")
            return redirect(url_for("library.user_library"))

        db.session.delete(pdf)
        db.session.commit()
        flash("PDF deleted.", "info")
        return redirect(url_for("library.user_library"))



@bp.route("/download/<string:kind>/<filename>")
@login_required
def download_pdf(kind, filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    # Make sure we have an absolute path
    if not os.path.isabs(upload_folder):
        upload_folder = os.path.join(current_app.root_path, upload_folder)

    safe_path = safe_join(upload_folder, filename)
    if not os.path.exists(safe_path):
        flash("File not found.", "danger")
        return redirect(url_for("library.user_library"))

    return send_from_directory(upload_folder, filename, as_attachment=True)


