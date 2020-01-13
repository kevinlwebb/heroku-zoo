from app.tables import Animal, User

from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, RadioField
from wtforms.fields.html5 import DateTimeLocalField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Required

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class AnimalForm(FlaskForm):
    name = StringField('Animal Name', validators=[DataRequired()])
    typ = SelectField(u'Animal Type', choices=[('Elephant', 'Elephant'), ('Monkey', 'Monkey'), ('Giraffe', 'Giraffe')])
    submit = SubmitField('Add')

    def validate_username(self, name):
        animal = Animal.query.filter_by(name=name.data).first()
        if animal is not None:
            raise ValidationError('Animal name already exists.')


class TimeForm(FlaskForm):
    #time = StringField('Animal Name', validators=[DataRequired()])
    date = DateTimeLocalField('Select date and time next scheduled feed', format='%m/%d/%y')
    #feeder = SelectField(u'Animal Type', choices=[('Elephant', 'Elephant'), ('Monkey', 'Monkey'), ('Giraffe', 'Giraffe')])
    submit = SubmitField('Add')