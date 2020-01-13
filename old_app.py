#!/usr/bin/env python

import json
import time
import socket
import os
import logging
import random

from datetime import datetime, timedelta,date

from flask import Flask, render_template, flash, redirect, url_for, request
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, RadioField
from wtforms.fields.html5 import DateTimeLocalField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Required

from werkzeug.urls import url_parse
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship 

# Logger
#logger = logging.basicConfig(filename='zoo.log', format='%(levelname)s:%(asctime)s:%(message)s', level=logging.DEBUG)
handler = logging.FileHandler("zoo.log")
formatter = logging.Formatter('%(levelname)s:%(asctime)s:%(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger('zoo')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


app = Flask(__name__)


basedir = os.path.abspath(os.path.dirname(__file__))

# Global Variables

feeders = {1:{
	"schedule":[],
	"wifi":"connected",
	"activation":"Activated"
},
2:{
	"schedule":[],
	"wifi":"connected",
	"activation":"Activated"
},
3:{
	"schedule":[],
	"wifi":"not connected",
	"activation":"Deactivated"
}
}

last_daily_schedule_creation = datetime(1, 1, 1, 0, 0, 0)

#####
# sqlalchemy
'''
Base = declarative_base()


class Animal(Base):
    __tablename__ = 'animal'
    name = Column(String(80), unique=True, nullable=False, primary_key=True)
    typ = Column(String(150))

    def __repr__(self):
        return "<Name: {}>".format(self.name)

engine = create_engine('sqlite:///zoo.db')

Base.metadata.bind = engine

session = scoped_session(sessionmaker(bind=engine))
'''
#####
# flask_sqlalchemy

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

'''
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
        animal = session.query(Animal).filter_by(name=name.data).first()
        if animal is not None:
            raise ValidationError('Animal name already exists.')


class TimeForm(FlaskForm):
    #time = StringField('Animal Name', validators=[DataRequired()])
    date = DateTimeLocalField('Select date and time next scheduled feed', format='%m/%d/%y')
    #feeder = SelectField(u'Animal Type', choices=[('Elephant', 'Elephant'), ('Monkey', 'Monkey'), ('Giraffe', 'Giraffe')])
    submit = SubmitField('Add')
    '''

'''
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    tier = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Animal(db.Model):
    name = Column(String(80), unique=True, nullable=False, primary_key=True)
    typ = Column(String(150))

    def __repr__(self):
        return "<Name: {}>".format(self.name)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)
'''

from tables import User, Animal, Post
from forms import LoginForm, RegistrationForm, AnimalForm, TimeForm

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_first_request
def create_tables():
    db.create_all()
    user = User.query.filter_by(username='admin').first()
    if user is None:
        user = User(username='admin', email='kevinlwebb03@gmail.com',first_name='admin',last_name='zoo',tier='Admin')
        user.set_password('admin1234')
        db.session.add(user)
        db.session.commit()

    animal = Animal.query.all()
    if not animal:
        animal = Animal(name='Kirby', typ='Elephant')
        db.session.add(animal)
        db.session.commit()

    '''
    if not engine.dialect.has_table(engine, 'animal'):  # If table don't exist, create.
        Base.metadata.create_all(engine)
        # Insert an animal in the book table
        print('[CREATE TABLE]')
        animal = Animal(name='Kirby', typ='Elephant')
        session.add(animal)
        session.commit()
        print('[FINISHED TABLE]')
    '''


'''
@app.teardown_request
def remove_session(ex=None):
    session.remove()
'''


@app.route('/index')
@login_required
def index():
	completed,notifications = getcompletedschedule()
	return render_template('dashboard.html', title='Home',feeder=feeders,complete=completed,notifications=notifications)


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login2.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    #if current_user.is_authenticated:
    #    return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, first_name=form.first_name.data,last_name=form.last_name.data,tier='General')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, '+ user.username +' is now a registered user!')
        logger.info('%s registered new user: %s', current_user.username, form.username.data)
        return redirect(url_for('users'))
    return render_template('register2.html', title='Register', form=form)


@app.route('/users')
@login_required
def users():
    users = None
    users = User.query.all()
    db.session.commit()
    completed,notifications = getcompletedschedule()
    return render_template("users.html", users=users,complete=completed,notifications=notifications)


@app.route('/log')
@login_required
def log():
    events = []
    with open("zoo.log", 'r') as f:
        for line in f:
            events.append(line)
    completed,notifications = getcompletedschedule()
    return render_template("log.html", events=events,complete=completed,notifications=notifications)


@app.route('/schedule')
@login_required
def schedule():
	completed,notifications = getcompletedschedule()
	return render_template("schedule.html", feeder = feeders,complete=completed,notifications=notifications)


@app.route('/addschedule', methods=['GET', 'POST'])
@login_required
def addschedule():
    form = TimeForm()
    print(form.validate_on_submit())
    if request.form:
        in_date = request.form['date'].replace("T"," ")
        feeder_num = request.form.getlist("users")
        print(feeder_num)
        datetime_object = datetime.strptime(in_date, '%Y-%m-%d %H:%M')
        for f in feeder_num:
            feeders[int(f)]["schedule"].append(datetime_object)
        #datetime_object = datetime.strptime(in_date, '%Y-%m-%d %H:%M')
        #feeders[1]["schedule"].append(datetime_object)
        return redirect(url_for('schedule'))
    	#%m/%d/%y
    	#return redirect(url_for('schedule'))

    if form.validate_on_submit():
        #animal = Animal(name=form.name.data, typ=form.typ.data)
        #session.add(animal)
        #session.commit()
        #flash(animal.name +' is now a registered user!')
        #logger.info('%s registered new user: %s', current_user.username, form.name.data)

        #feeders[1]["schedule"].append(datetime.now() + timedelta(minutes=1))
		#print(feeders[1]["schedule"])
        
        print(form.date.data)

        return redirect(url_for('schedule'))
    return render_template('addtime.html', title='Register', form=form)


@app.route("/delete", methods=["POST"])
@login_required
def delete():
    username = request.form.get("username")
    user = User.query.filter_by(username=username).first()
    db.session.delete(user)
    db.session.commit()
    logger.info('%s deleted user: %s', current_user.username, username)
    return redirect(url_for('users'))


@app.route('/animals', methods=["GET", "POST"])
@login_required
def animals():
    animals = None
    if request.form:
        try:
            animal = Animal(name=request.form.get("name"), typ=request.form.get("typ"))
            db.session.add(animal)
            db.session.commit()

        except Exception as e:
            print("Failed to add animals")
            print(e)
    try:
        animals = Animal.query.all()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise
    completed,notifications = getcompletedschedule()
    return render_template("animals.html", animals=animals,complete=completed,notifications=notifications)


@app.route("/updateanimal", methods=["POST"])
@login_required
def updateanimal():
    try:
        newname = request.form.get("newname")
        oldname = request.form.get("oldname")
        animal = Animal.query.filter_by(name=oldname).first()
        animal.name = newname
        db.session.commit()

    except Exception as e:
        print("Couldn't update animal name")
        print(e)

    return redirect("/animals")


@app.route("/deleteanimal", methods=["POST"])
@login_required
def deleteanimal():
    name = request.form.get("name")
    animal = Animal.query.filter_by(name=name).first()
    db.session.delete(animal)
    db.session.commit()
    logger.info('%s deleted animal: %s', current_user.username, name)
    return redirect("/animals")


@app.route('/addanimal', methods=['GET', 'POST'])
@login_required
def addanimal():
    form = AnimalForm()
    if form.validate_on_submit():
        animal = Animal(name=form.name.data, typ=form.typ.data)
        db.session.add(animal)
        db.session.commit()
        flash(animal.name +' is now a registered user!')
        logger.info('%s registered new user: %s', current_user.username, form.name.data)
        return redirect(url_for('animals'))
    return render_template('addanimal.html', title='Register', form=form)


@app.route("/addtime/<feeder_id>", methods=["POST"])
@login_required
def addtime(feeder_id):

    feeder_id = int(feeder_id)
    global feeders
    feeders[feeder_id]["schedule"].append(datetime.now() + timedelta(minutes=1))
    sendSchedule(bytes(feeders[feeder_id]["schedule"][-1].strftime("%m/%d/%Y, %H:%M:%S").encode()))

    return str(datetime.now() + timedelta(minutes=1))


@app.route("/deletetime", methods=["POST"])
@login_required
def deletetime():
    feeder_id = int(request.form.get("feeder_id"))
    time = request.form.get("time")
    global feeders
    if "." in time:
        index = feeders[feeder_id]["schedule"].index(datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f"))
    else:
        index = feeders[feeder_id]["schedule"].index(datetime.strptime(time, "%Y-%m-%d %H:%M:%S"))
    print(index)
    del feeders[feeder_id]["schedule"][index]
    logger.info('%s deleted time, %s, on Feeder %s', current_user.username, time, feeder_id)
    return redirect("/schedule")


@app.route("/createdailyschedule")
@login_required
def createdailyschedule():
    global last_daily_schedule_creation
    if datetime.now().date() > last_daily_schedule_creation.date():
        global feeders
        feeds = random.randint(3,8)

        feeding_time_ranges = [(5,7),(10,13),(15,16),(18,24)]

        bins = pidgeon_hole(feeds, len(feeding_time_ranges))

        for feeding_time_range, b in zip(feeding_time_ranges, bins):
            start, end = feeding_time_range
            today = date.today()
            start_time = datetime(today.year, today.month, today.day, start, 0, 0)
            if end == 24:
                end_time = today + timedelta(days=1)
                end_time = datetime(end_time.year, end_time.month, end_time.day, 0, 0, 0)
            else:
                end_time = datetime(today.year, today.month, today.day, end, 0, 0)
            for time in randomtimes(start_time, end_time, b):
                feeders[random.randint(1,3)]["schedule"].append(time)
        
        last_daily_schedule_creation = datetime.now()

        logger.info('%s initiated daily schedule creation', current_user.username)
        
    return redirect("/schedule")


@app.route("/getschedule", methods=["GET"])
def getschedule():
	global feeders
	return json.dumps(feeders,default=json_serial)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def getcompletedschedule():
	global feeders
	out = {}
	notifications = 0
	for key,value in feeders.items():
		out[key] = []
		for i,date in enumerate(value["schedule"]):
			if datetime.now() > date:
				notifications += 1
				out[key].append(date)
	return out,notifications


def sendSchedule(message):
    s = socket.socket()

    # Define the port on which you want to connect 
    port = 12345

    try:
        print("Not Implemented")
        # connect to the server on local computer 
        #s.connect(('ip address', port))

        # send a thank you message to the client.  
        #s.send(message)

        # close the connection 
        #s.close()
    except Exception as e:
        print("Couldn't send time")
        print(e)


def randomtimes(stime, etime, n):
    td = etime - stime
    return [random.random() * td + stime for _ in range(n)]


def pidgeon_hole(n, n_bins): 
    quotient = n // n_bins
    remainder = n % n_bins

    bins = [quotient for i in range(n_bins)]    
    for i in range(remainder):
        bins[i] += 1
    return bins


if __name__ == "__main__": 
	app.run(host='0.0.0.0', debug=True)
