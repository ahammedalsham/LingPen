from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Course, CourseRegistration
from app.forms import CourseForm
from app.decorators import admin_required
#from app.mailer import send_course_enrollment

bp = Blueprint("courses", __name__, template_folder='../../templates/courses')

@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    courses = Course.query.order_by(Course.created_at.desc()).paginate(page=page, per_page=9)
    return render_template("courses/index.html", courses=courses)

@bp.route("/<int:course_id>")
def detail(course_id):
    course = Course.query.get_or_404(course_id)
    user_is_enrolled = False
    if current_user.is_authenticated:
        user_is_enrolled = CourseRegistration.query.filter_by(user_id=current_user.id, course_id=course.id).first() is not None
    return render_template("courses/detail.html", course=course, user_is_enrolled=user_is_enrolled)

@bp.route("/create", methods=["GET","POST"])
@login_required
@admin_required
def create():
    form = CourseForm()
    if form.validate_on_submit():
        c = Course(title=form.title.data.strip(), description=form.description.data.strip(), is_live=form.is_live.data)
        db.session.add(c)
        db.session.commit()
        flash('Course created.', 'success')
        return redirect(url_for('courses.detail', course_id=c.id))
    return render_template("courses/create.html", form=form)

@bp.route("/<int:course_id>/edit", methods=["GET","POST"])
@login_required
@admin_required
def edit(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.title = form.title.data.strip()
        course.description = form.description.data.strip()
        course.is_live = form.is_live.data
        db.session.commit()
        flash('Course updated.', 'success')
        return redirect(url_for('courses.detail', course_id=course.id))
    return render_template("courses/edit.html", form=form, course=course)

@bp.route("/<int:course_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted.', 'info')
    return redirect(url_for('courses.index'))

@bp.route("/<int:course_id>/enroll", methods=["POST"])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    existing = CourseRegistration.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if existing:
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('courses.detail', course_id=course.id))
    reg = CourseRegistration(user_id=current_user.id, course_id=course.id)
    db.session.add(reg)
    db.session.commit()
    #send_course_enrollment(current_user, course)
    flash('Enrolled successfully 🎉', 'success')
    return redirect(url_for('courses.detail', course_id=course.id))
