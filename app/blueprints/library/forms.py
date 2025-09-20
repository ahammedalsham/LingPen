# app/library/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

class PDFUploadForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description")
    file = FileField("Upload PDF", validators=[DataRequired(), FileAllowed(["pdf"], "PDFs only!")])
    submit = SubmitField("Upload")
