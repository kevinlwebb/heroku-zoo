from app import app, db, login
from app.tables import User, Animal, Feeder, Date
from flask_login import login_required, current_user, login_user, logout_user
# LoginManager, UserMixin, login_user, logout_user
from flask import Flask, render_template, redirect, url_for, flash, request
from app.forms import LoginForm, RegistrationForm, AnimalForm, TimeForm
from werkzeug.urls import url_parse
from datetime import datetime, timedelta,date
import logging
import random
import json
import socket

from apscheduler.schedulers.background import BackgroundScheduler


# Logger
#logger = logging.basicConfig(filename='zoo.log', format='%(levelname)s:%(asctime)s:%(message)s', level=logging.DEBUG)
handler = logging.FileHandler("zoo.log")
formatter = logging.Formatter('%(levelname)s:%(asctime)s:%(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger('zoo')
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


last_daily_schedule_creation = datetime(1, 1, 1, 0, 0, 0)


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

    feeder = Feeder.query.all()
    if not feeder:
        feeder1 = Feeder(number=1,wifi="Connected",activation="Activated")
        feeder2 = Feeder(number=2,wifi="Connected",activation="Activated")
        feeder3 = Feeder(number=3,wifi="Connected",activation="Activated")
        db.session.add(feeder1)
        db.session.add(feeder2)
        db.session.add(feeder3)
        db.session.commit()


@app.route('/index')
@login_required
def index():
	completed,notifications = getcompletedschedule()
	return render_template('dashboard.html', title='Home',feeder=Feeder.as_dict(),complete=completed,notifications=notifications)


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        completed,notifications = getcompletedschedule()
        return render_template('dashboard.html', title='Home',feeder=Feeder.as_dict(),complete=completed,notifications=notifications)
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
            completed,notifications = getcompletedschedule()
            return render_template('dashboard.html', title='Home',feeder=Feeder.as_dict(),complete=completed,notifications=notifications)
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
            feeder = Feeder.query.filter_by(number=int(f)).first()
            date = Date(date=datetime_object,feeder=feeder)
            db.session.add(date)
            db.session.commit()
        return redirect("/")
    if form.validate_on_submit():
        print(form.date.data)
        return redirect("/")
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


@app.route("/deletetime", methods=["POST"])
@login_required
def deletetime():
    feeder_id = int(request.form.get("feeder_id"))
    time = request.form.get("time")
    if "." in time:
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")
    else:
        time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
    date = Date.query.filter_by(feeder_id=feeder_id,date=time).first()
    db.session.delete(date)
    db.session.commit()

    logger.info('%s deleted time, %s, on Feeder %s', current_user.username, time, feeder_id)
    return redirect("/")


@app.route("/createdailyschedule")
@login_required
def createdailyschedule():

    num_feeders = len(Feeder.query.all())
    for x in range(num_feeders):
        dates = Date.query.filter_by(feeder_id=x+1).all()
        for d in dates:
            db.session.delete(d)
            db.session.commit()

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
            num_feeders = len(Feeder.query.all())
            feeder = Feeder.query.filter_by(number=random.randint(1,num_feeders)).first()
            date1 = Date(date=time,feeder=feeder)
            db.session.add(date1)
            db.session.commit()

    logger.info('%s initiated daily schedule creation', current_user.username)
        
    return redirect("/")


@app.route("/getschedule", methods=["GET"])
def getschedule():
    feeders = Feeder.as_dict()
    return json.dumps(feeders,default=json_serial)


@app.route("/addfeeder")
@login_required
def addfeeder():
    feeder = Feeder(number=len(Feeder.query.all())+1,wifi="Connected",activation="Activated")
    db.session.add(feeder)
    db.session.commit()
    logger.info('%s added feeder.', current_user.username)
    return redirect("/")


@app.route("/deletefeeder", methods=["POST"])
@login_required
def deletefeeder():
    feeder_id = int(request.form.get("feeder_id"))
    feeder = Feeder.query.filter_by(number=feeder_id).first()
    db.session.delete(feeder)
    db.session.commit()

    logger.info('%s deleted Feeder %s', current_user.username, feeder_id)
    return redirect("/")

@app.route("/test")
def test():
    #return render_template('testjinja.html')
    return "hi"


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))


def getcompletedschedule():
    feeders = Feeder.as_dict()
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

def daily_scheduler():

    num_feeders = len(Feeder.query.all())
    for x in range(num_feeders):
        dates = Date.query.filter_by(feeder_id=x+1).all()
        for d in dates:
            db.session.delete(d)
            db.session.commit()

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
            num_feeders = len(Feeder.query.all())
            feeder = Feeder.query.filter_by(number=random.randint(1,num_feeders)).first()
            date1 = Date(date=time,feeder=feeder)
            db.session.add(date1)
            db.session.commit()

scheduler = BackgroundScheduler(timezone="America/Chicago")
#job = scheduler.add_job(daily_scheduler, 'interval', minutes=1)
job = scheduler.add_job(daily_scheduler, trigger='cron', hour='00', minute='01')
scheduler.start()