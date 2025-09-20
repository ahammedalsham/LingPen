from flask import Blueprint, render_template, request, flash, redirect, url_for

bp = Blueprint("general", __name__, template_folder='../../templates/general')

@bp.route("/about")
def about():
    return render_template("about.html")

@bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # Handle form submission logic here (send email, store contact message)
        flash("Your message has been sent!", "success")
        return redirect(url_for("general.contact"))
    return render_template("contact.html")

@bp.route("/faq")
def faq():
    return render_template("faq.html")