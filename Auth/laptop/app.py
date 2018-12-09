import flask
import arrow  # Replacement for datetime, based on moment.js
import acp_times  # Brevet time calculations
import config
import logging
import os
import time
import json
import csv
from flask import Flask, redirect, url_for, request, render_template, abort, jsonify
import pymongo
from pymongo import MongoClient
from flask_restful import Resource, Api, reqparse, marshal_with, fields
from flask_login import LoginManager, current_user, login_required, login_user, logout_user, UserMixin
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import PasswordField, StringField, SubmitField, BooleanField, validators
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from functools import wraps


#INITIALIZATION, EXTENSIONS, AND GLOBALS_____
app = Flask(__name__)
api = Api(app)
CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY
client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'], 27017)
myDB = client["Brevet-Database"]
login_manager = LoginManager()
login_manager.setup_app(app)
nextUserId = 0
csrf = CSRFProtect(app)
USERS = {} 


#USER REGISTRATION/LOGIN_____________________
@login_manager.unauthorized_handler                     # If the user tries to request a page that has the login_required decorator it will redirect to the login page
def unauthorized():
    abort(401)

@login_manager.user_loader                              # Loads the user object from the user ID stored in the session.
def load_user(user_id):
    global USERS
    for i in range(len(USERS)):
        if user_id == str(USERS[i].id):
            return USERS[i]
    return None

class User(UserMixin):                                  # User class. Inherits from UserMixin which gives us standard implementations of the basic user methods
    def __init__(self, name, user_id, password, active=True):
        self.name = name
        self.id = user_id
        self.password = password
        self.active = active

    def is_active(self):
        return self.active

    def check_password(self, pas):
        return check_password_hash(self.password, pas)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        global USERS
        for i in range(len(USERS)):
            if str(data['id']) == str(USERS[i].id):
                return USERS[i]
        return None

class RegistrationForm(FlaskForm):
    username    = StringField('Username', [validators.required(), validators.Length(min=1)])
    password    = PasswordField('New Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords must match'), validators.Length(min=8, message='Password must be at least 8 characters long.')])
    confirm     = PasswordField('Repeat Password')
    submit      = SubmitField('Register')

    def validate_username(self, username):              # Custom validation to check if the username is taken
        global USERS
        username = RegistrationForm().username.data
        for i in range(len(USERS)):
            if username == USERS[i].name:
                raise validators.ValidationError('Please use a different username.')

class LoginForm(FlaskForm):
    username    = StringField('Username', [validators.required(), validators.Length(min=1)])
    password    = PasswordField('Password', [validators.DataRequired(), validators.Length(min=8, message='Are you sure that password was long enough?')])
    submit      = SubmitField('Login')
    remember_me = BooleanField('Remember me')


#CUSTOM WRAPPERS_____________________________
def require_api_token(func):
    @wraps(func)
    def check_token(*args, **kwargs):
        if request.authorization is not None:                                               # Request is not from the front-end
            if User.verify_auth_token(request.authorization['username']) is None:           # The token they provided was invalid
                abort(401)                                                                  # Unauthorized
            return func(*args, **kwargs)                                                    # Otherwise just send them where they wanted to go
        else:                                                                               # Request is from the front end
            if 'api_session_token' not in flask.session:                                    # If the user's token isn't in their session
                abort(401)                                                                  # Unauthorized
            if current_user.verify_auth_token(flask.session['api_session_token']) is None:  # Verify that the token is valid and is not expired
                abort(401)                                                                  # Unauthorized
        return func(*args, **kwargs)                                                        # Otherwise just send them where they wanted to go
    return check_token


#API RESOURCES_______________________________
class listAll(Resource):
    method_decorators = [require_api_token]
    listAllFields = {
        'km': fields.Integer,
        'open_time': fields.String,
        'close_time': fields.String
    }
    @marshal_with(listAllFields)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('top', type=int)
        arg = parser.parse_args()
        if arg.get('top', 0) is None:
            arg = 20
        else:
            arg = arg['top']
        cpFind = myDB["checkpoints"]
        _items = cpFind.find()
        items = []
        for item in _items:
            if arg is 0:
                break
            items.append(item)
            arg -= 1
        return items
api.add_resource(listAll, '/listAll', '/listAll/json', '/listAll/', '/listAll/json/')

class listOpenOnly(Resource):
    method_decorators = [require_api_token]
    listOpenFields = {
        'km': fields.Integer,
        'open_time': fields.String
    }
    @marshal_with(listOpenFields)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('top', type=int)
        arg = parser.parse_args()
        if arg.get('top', 0) is None:
            arg = 20
        else:
            arg = arg['top']
        cpFind = myDB["checkpoints"]
        _items = cpFind.find()
        items = []
        for item in _items:
            if arg is 0:
                break
            items.append(item)
            arg -= 1
        return items
api.add_resource(listOpenOnly, '/listOpenOnly', '/listOpenOnly/json', '/listOpenOnly/', '/listOpenOnly/json/')

class listCloseOnly(Resource):
    method_decorators = [require_api_token]
    listCloseFields = {
        'km': fields.Integer,
        'close_time': fields.String
    }
    @marshal_with(listCloseFields)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('top', type=int)
        arg = parser.parse_args()
        if arg.get('top', 0) is None:
            arg = 20
        else:
            arg = arg['top']
        cpFind = myDB["checkpoints"]
        _items = cpFind.find()
        items = []
        for item in _items:
            if arg is 0:
                break
            items.append(item)
            arg -= 1
        return items
api.add_resource(listCloseOnly, '/listCloseOnly', '/listCloseOnly/json', '/listCloseOnly/', '/listCloseOnly/json/')

class listAllCsv(Resource):
    method_decorators = [require_api_token]
    def get(self):
        allJson = listAll.get(listAll)
        return csvify(allJson)
api.add_resource(listAllCsv, '/listAll/csv', '/listAll/csv/')

class listOpenOnlyCsv(Resource):
    method_decorators = [require_api_token]
    def get(self):
        openJson = listOpenOnly.get(listOpenOnly)
        return csvify(openJson)
api.add_resource(listOpenOnlyCsv, '/listOpenOnly/csv', '/listOpenOnly/csv/')

class listCloseOnlyCsv(Resource):
    method_decorators = [require_api_token]
    def get(self):
        closeJson = listCloseOnly.get(listCloseOnly)
        return csvify(closeJson)
api.add_resource(listCloseOnlyCsv, '/listCloseOnly/csv', '/listCloseOnly/csv/')


#APP ROUTES__________________________________
@app.route('/submit', methods=['POST'])
def submit():
    data = request.form                             # Create variable 'data' and populate it with the raw form data
    miles = []                                      # Initialize list miles to hold all miles values
    km = []                                         # Initialize list km to hold all km values
    location = []                                   # Initialize list location to hold all location values
    open_times = []                                 # Initialize list open_times to hold all open time values
    close_times = []                                # Initialize list close_times to hold all close time values
    size = 0                                        # Initialize size for number of checkpoints in request
    for key in data.keys():                         # For each key that appears in the form data
        for value in data.getlist(key):             # For each value of each key
            if key == 'miles' and value != '':      # If the key is miles and it has a value
                miles.append(value)                 # Add that value to the miles list
                size += 1                           # Update size as long as there are still values
            elif key == 'km' and value != '':       # Repeat for all other keys...
                km.append(value)
            elif key == 'open' and value != '':
                open_times.append(value)
            elif key == 'close' and value != '':
                close_times.append(value)
            elif key == 'distance':
                dist = value                        # Create a variable with distance value
    i = 0
    for value in data.getlist('location'):          # For every value with the location key
        location.append(value)                      # Add the location value to its list
        i += 1
        if i == size:                               # Don't want to add a bunch of null locations to that list
            break
    cpcol = myDB["checkpoints"]                     # Get the "checkpoints" collection from our database
    cpcol.drop()                                    # Clear all the stuff in the database before inserting new stuff
    insertCol = myDB["checkpoints"]                 # Create a new collection with the name "checkpoints" to insert our data into and store it in 'insertCol'
    for x in range(size):
        item_doc = {                                # Create a single item to be added to the database
           'distance': dist,                        # Add distance to the database
           'miles': miles[x],                       # Add each of the items extracted from the form data in key-value pairs
           'km': km[x],
           'location': location[x],
           'open_time': open_times[x],
           'close_time': close_times[x]
        }
        insertCol.insert_one(item_doc)              # Add current item to the  database
        dist = ""                                   # Give dist a null value so it's only passed in once
    return render_template('calc.html', reload=1)   # "Keep going"

@app.route('/done')
def display():
    cpFind = myDB["checkpoints"]
    _items = cpFind.find()
    items = [item for item in _items]
    return render_template('display.html', items=items)

@app.route("/")
@app.route("/index")
def index():
    cpCount = myDB["checkpoints"]
    if cpCount.count() is not 0:
        return flask.render_template('calc.html', reload=1)
    return flask.render_template('calc.html', reload=0)

@app.route("/logout") 
@login_required
def logout():
    logout_user()
    flask.session.pop('api_session_token', None)
    return redirect(url_for('index'))

@csrf.exempt
@app.route('/api/register', methods = ['POST'])
def register_user():
    username = request.json.get('username')
    password = request.json.get('password')
    global USERS
    global nextUserId
    if username is None or password is None:
        abort(400)
    user = load_user_from_name(username)
    if user:
        abort(400)                                                          # Someone already has that username
    if len(str(password)) < 8:
        abort(400)                                                          # Password is too short
    usrAdd = myDB["users"]
    hashPass = generate_password_hash(password)
    user = {"username": username, "password": hashPass, "id": str(nextUserId)}
    usrAdd.insert_one(user)
    userInstance = User(name=username, user_id=str(nextUserId), password=hashPass)       # Create an instance of the user class
    USERS[nextUserId] = userInstance
    nextUserId = nextUserId + 1
    return jsonify({ 'username': userInstance.name }), 201, {'Location': url_for('get_user', id = userInstance.id, _external = True)}

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()                           # Get the registration form and store it in 'form'
    if form.validate_on_submit():                       # If register was called with user data to register and that data is valid
        username = form.username.data
        usrAdd = myDB["users"]
        hashPass = generate_password_hash(form.password.data)
        global nextUserId
        user = {"username": username, "password": hashPass, "id": str(nextUserId)}
        usrAdd.insert_one(user)
        userInstance = User(name=username, user_id=str(nextUserId), password=hashPass)     # Create an instance of the user class
        global USERS
        USERS[nextUserId] = userInstance
        nextUserId = nextUserId + 1
        return redirect(url_for('login'))
    return flask.render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        abort(400)
    form = LoginForm(request.form)
    if form.validate_on_submit():
        global USERS
        username = form.username.data
        user = load_user_from_name(username)
        if user is None:
            return flask.render_template('login.html', form=form)
        else:
            login_user(user, form.remember_me.data)

        token = current_user.generate_auth_token()                  # Generate a token for the logged in user
        token = str(token)
        token = token[2:]
        token = token[:-1]
        flask.session['api_session_token'] = token                  # Store that token as a session variable
        
        nextUrl = flask.request.args.get('next')
        if nextUrl is None:
            return flask.redirect(flask.url_for('index'))
        if is_safe_url(nextUrl):
            return flask.redirect(nextUrl)
        return flask.abort(400)
    return flask.render_template('login.html', form=form)

@app.route('/api/token')
def get_token():
    if request.authorization is not None:
        i = validate(request.authorization['username'], request.authorization['password']) #Check for username and password first
    else: 
        i = validate("fail", "a") #Guaranteed to fail if user is not logged in and there is no active session token
    if i is 1 or i is 2:
        return jsonify({'token': str(flask.session['api_session_token']), 'duration': 600})
    if i is 3:
        u = load_user_from_name(request.authorization['username'])
        token = u.generate_auth_token()
        token = str(token)
        token = token[2:]
        token = token[:-1]
        app.logger.debug(token)
        return jsonify({'token': token, 'duration': 600})
    if i is 4:
        u = User.verify_auth_token(request.authorization['username'])
        token = u.generate_auth_token()
        token = str(token)
        token = token[2:]
        token = token[:-1]
        return jsonify({'token': token, 'duration': 600})
    abort(401)

@app.route('/api/users/<int:id>')
def get_user(id):
    if validate(request.authorization['username'], request.authorization['password']) is 0:
        abort(401)
    global USERS
    user = USERS[id]
    if not user:
        abort(400)
    return jsonify({'username': user.name})


#AJAX REQUEST HANDLERS (returns json)________
@app.route("/_calc_times")
def _calc_times():
    km = request.args.get('km', -1, type=float)                         # Retrieve the km val passed in. Default to -1
    begin_time = request.args.get('begin_time')                         # Retrieve the begin_time val passed in
    begin_date = request.args.get('begin_date')                         # Retrieve the begin_date val passed in
    distance = request.args.get('distance')                             # Retrieve the distance val passed in

    if km == -1:                                                        # Empty string was passed in
        result = {"error": 2}                                           # Error two tells calc.html to clear the empty row
        return flask.jsonify(result=result)                             # Abort now with error

    distance = float(distance)                                          # Convert distance form string to float so we can perform operations on it
    if km > distance * 1.2:                                             # More than 20% greater than the total brevet length is our cutoff
        result = {"error": 1}                                           # Error 1 tells calc.html the new value was too big
        return flask.jsonify(result=result)                             # Abort now with error

    time = begin_date + " " + begin_time
    open_time = acp_times.open_time(km, distance, time)
    close_time = acp_times.close_time(km, distance, time)
    long_enough = (km >= distance)

    result = {"open": open_time, "close": close_time, "error": 0, "enough": long_enough}
    return flask.jsonify(result=result)


#ERROR HANDLERS______________________________
@app.errorhandler(404)
def page_not_found(error):
    flask.session['linkback'] = flask.url_for("index")
    return flask.render_template('404.html'), 404

@app.errorhandler(400)
def bad_request(error):
    flask.session['linkback'] = flask.url_for("index")
    return flask.render_template('400.html'), 400

@app.errorhandler(401)
def not_authorized(error):
    flask.session['linkback'] = flask.url_for("index")
    return flask.render_template('401.html'), 401


#HELPER FUNCTIONS____________________________
def csvify(temp):
    all_csv = open('toList.csv', 'w')
    csvwriter = csv.writer(all_csv)
    count = 0
    for thing in temp:
        if count == 0:
            header = thing.keys()
            csvwriter.writerow(header)
            count += 1
        csvwriter.writerow(thing.values())
    all_csv.close()
    all_csv = open('toList.csv', 'r')
    return flask.Response(all_csv, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=toList.csv"})

def populate_USERS():
    global USERS
    global nextUserId
    users_collection = myDB["users"]
    for document in users_collection.find():
        username = document["username"]
        hashPass = document["password"]
        userInstance = User(username, str(nextUserId), hashPass)
        USERS[nextUserId] = userInstance
        nextUserId = nextUserId + 1

def print_all_users(place): # For debugging
    if place == 'database':
        app.logger.debug("Printing the users in myDB.")
        users_collection = myDB["users"]
        for document in users_collection.find():
            app.logger.debug("Username: " + document["username"] + " Id: " + str(document["id"]) + " Hashed password: " + document["password"])
    elif place == 'USERS':
        app.logger.debug("Printing the users in USERS.")
        global USERS
        for i in range(len(USERS)):
            app.logger.debug("Username: " + USERS[i].name + " Id: " + str(USERS[i].id) + " Hashed password: " + USERS[i].password)
    else:
        app.logger.debug("The 'place' value was invalid.")

def validate(flex, password):
    global USERS
    # First check if they're logged in
    if current_user.is_authenticated:
        return 1
    # Then check for a token
    if 'api_session_token' in flask.session:
        if current_user.verify_auth_token(flask.session['api_session_token']) is not None:
                return 2
    # Next try to validate with username and password from the GET args
    u = load_user_from_name(flex)
    if u is not None:
        if u.check_password(pas=password):
            return 3 
    # Finally try to validate with a token
    if User.verify_auth_token(flex) is not None:
        return 4
    #If all of these fail the request is not valid
    return 0

def load_user_from_name(username): # Returns the user object correspoding to the username passed in
    global USERS
    for i in range(len(USERS)):
        if username == str(USERS[i].name):
            return USERS[i]
    return None


#SETUP_______________________________________
app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    populate_USERS()
    app.run(host='0.0.0.0', port=80, debug=True)
