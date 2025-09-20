from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, IntegerField, SubmitField, FileField, DateField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange, Email
from wtforms.fields import DateTimeLocalField

# Auth forms
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create account')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class ForgotForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send reset link')

class ResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Set new password')

# Post/Blog forms
class PostForm(FlaskForm):
    body = TextAreaField('Write your post', validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField('Publish')

class BlogForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=255)])
    body = TextAreaField('Write your blog', validators=[DataRequired()])
    submit = SubmitField('Publish')

class CommentForm(FlaskForm):
    body = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField('Comment')

# Events & Courses forms
class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    date = DateTimeLocalField('Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    image = StringField('Image URL')
    is_online = BooleanField('Online Event')
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1, max=100000)])
    submit = SubmitField('Save Event')

class CourseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    is_live = BooleanField('Live Course')
    submit = SubmitField('Save Course')

# New Profile Editing Form
class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[Length(max=80)])
    last_name = StringField('Last Name', validators=[Length(max=80)])
    dob = DateField('Date of Birth', format='%Y-%m-%d')
    photo = FileField('Profile Picture')       # Accept photo upload
    cover = FileField('Cover Image')           # Accept cover image upload
    about = TextAreaField('About', validators=[Length(max=1000)])
    primary_language = StringField('Primary Language', validators=[Length(max=80)])
    interests = StringField('Interests', validators=[Length(max=255)])
    proficiency_level = StringField('Proficiency Level', validators=[Length(max=50)])
    submit = SubmitField('Save Profile')