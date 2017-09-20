"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, jsonify, render_template, redirect, request, flash,
                   session)
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Rating, Movie


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template('/homepage.html')

@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template('user_list.html',
                           users=users)


@app.route('/register', methods=['GET'])
def register_form():
    """Shows registration form."""

    return render_template('register_form.html')

@app.route('/process_registration', methods=['POST'])
def process_registration():

    email = request.form.get('email')
    password = request.form.get('password')
    zipcode = request.form.get('zipcode')
    age = int(request.form.get('age'))

    q = User.query.filter_by(email=email)

    if q.first():
        flash("You already registered")
        return redirect("/")

    else:
        user = User(email=email,
                    password=password,
                    zipcode=zipcode,
                    age=age)

        db.session.add(user)

        db.session.commit()
        flash("Successfully registered!")
        return redirect("/")


@app.route('/process_login', methods=['POST'])
def process_login():

    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        if user.password == password:

            session['user_id'] = user.user_id

            flash('Logged in!')
            return redirect('/')
        flash("Invalid password. Try again.")
        return redirect('/')
    else:
        flash('{} not found in our database. Please register!'.format(email))
        return redirect('/')

@app.route('/process_logout', methods=['POST'])
def process_logout():

    del session['user_id']
    flash('logged out successfully')
    return redirect('/')

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)



    app.run(port=5000, host='0.0.0.0')
