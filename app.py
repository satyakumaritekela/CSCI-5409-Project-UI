import os
import mysql.connector
import requests
import random
from flask import Flask, render_template, session, request, redirect, url_for

url_api = "http://tourismapplication-env.eba-crdb7ipg.us-east-1.elasticbeanstalk.com/apiv1"

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not password == confirm_password:
            return render_template('signup.html', error="Passwords mismatch")
        register_api = url_api + "/register/"
        r = requests.post(register_api, {"first_name":first_name, "last_name":last_name, "username":username, "password":password, "email":email})
        if r.status_code ==   200:
            session['user'] = username
            return redirect(url_for('login'))
        if r.status_code == 400:
            return render_template('signup.html', error=r.json().get('non_field_errors')[0])
        else:
            return render_template('signup.html', error="Some error occurred")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # if not re.match("[^@]+@[^@]+\.[^@]+", username):
        #     return render_template('login.html', error="Invalid username")
        print (username, password)
        login_api = url_api + "/login/"
        r = requests.post(login_api, {"username":username, "password":password})
        print (r.status_code)
        if r.status_code ==   200:
            session['user'] = username
            return redirect(url_for('authentication'))
        if r.status_code == 400:
            return render_template('login.html', error=r.json().get('non_field_errors')[0])
        else:
            return render_template('login.html', error="Some error occurred")
    return render_template('login.html')


@app.route('/authentication', methods=['GET', 'POST'])
def authentication():
    if request.method == 'POST':
        if not 'user' in session:
            return render_template('error.html')
        # if 'user' in session:
        username = session['user']
        otp = request.form.get('otp')
        authenticate_api = url_api + "/login-final/"
        r = requests.post(authenticate_api, {"username":username, "otp":otp})

        # print (r.status_code, str(r.content, 'utf-8'))

        if r.status_code ==   200:
            session['token'] = str(r.content)
            return redirect(url_for('dashboard'), code=307)
        if r.status_code == 400:
            return render_template('authentication.html', error="Invalid OTP")
        else:
            return render_template('authentication.html', error="Some error occurred")
    return render_template('authentication.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not 'token' in session:
        return render_template('error.html')
    ticket_api = url_api + "/list-booking/?token=" + str(session['token'])
    print (ticket_api)
    r = requests.get(ticket_api)
    if r.status_code == 200:
        print (r.json())
        return render_template('mytickets.html', ctx=r.json())
    return render_template('mytickets.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        keyword = request.form.get("keyword", '')
        print (keyword)
        if keyword:
            destinations = requests.get("http://trsdestinations.us-east-1.elasticbeanstalk.com/destinations?keyword=" + str(keyword))
            # print (destinations.json())
        else:
            destinations = requests.get("http://trsdestinations.us-east-1.elasticbeanstalk.com/destinations")
        return render_template('search.html', ctx=destinations.json())
    return render_template('search.html')


@app.route('/placedetail', methods=['GET', 'POST'])
def placedetail():
    idn = request.args.get('keyword', '')
    if not idn:
        return redirect(url_for('search'))

    destinations = requests.get("http://trsdestinations.us-east-1.elasticbeanstalk.com/destination_by_id?id=" + str(idn))
    return render_template('placedetail.html', desc=destinations.json()[0] )


@app.route('/bookticket', methods=['GET', 'POST'])
def bookticket():
    if not 'user' in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        destination = request.form.get('destination')
        bus_route = str(random.randint(1,10))
        number_of_passengers = request.form.get('nop')
        amount_paid = "40"
        card_details = request.form.get('carddetails')

        if not len(card_details.split("-")) == 4:
            return render_template('ticketbooking.html', username=username, destination=destination, error="Please eneter a valid CC")
        if not len(card_details) == 19:
            return render_template('ticketbooking.html', username=username, destination=destination, error="Please eneter a valid CC")

        booking_url = url_api + "/make-booking/"
        r = requests.post(booking_url, {"username":username, \
            "destination":destination, "bus_route":bus_route, \
            "number_of_passengers":number_of_passengers, "amount_paid":amount_paid})
        if r.status_code == 200:
            print ("SUCCESSSSS")
            return redirect(url_for("dashboard"))
        else:
            print (r.content)
            return render_template('ticketbooking.html', username=username, destination=destination, error="Some error occurred")

    idn = request.args.get('keyword', '')
    if not idn:
        return redirect(url_for('search'))
    destinations = requests.get("http://trsdestinations.us-east-1.elasticbeanstalk.com/destination_by_id?id=" + str(idn))
    return render_template('ticketbooking.html', destination=destinations.json()[0][1], username=session['user'])
