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


@app.route('/register')
def register_form():
    """Shows registration form."""

    return render_template('register_form.html')


@app.route('/process_registration', methods=['POST'])
def process_registration():
    """Checks if user is registered.  If not, adds user to database."""

    email = request.form.get('email')
    password = request.form.get('password')
    zipcode = request.form.get('zipcode')
    age = request.form.get('age')

    user = User.query.filter_by(email=email).first()

    if user:
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
        return redirect("/users/{}".format(user.user_id))


@app.route('/process_login', methods=['POST'])
def process_login():
    """Checks if user exists and verifies password."""
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        if user.password == password:

            session['user_id'] = user.user_id

            flash('Logged in!')
            return redirect('/users/{}'.format(user.user_id))
        flash("Invalid password. Try again.")
        return redirect('/')
    else:
        flash('{} not found in our database. Please register!'.format(email))
        return redirect('/')


@app.route('/process_logout', methods=['POST'])
def process_logout():
    """Ends current session."""

    del session['user_id']
    flash('logged out successfully')
    return redirect('/')


@app.route('/users/<user_id>')
def user_details(user_id):
    """Displays user details and movies rated by user."""

    user = User.query.filter_by(user_id=user_id).first()
    ratings = user.ratings
    age = user.age
    zipcode = user.zipcode

    return render_template('user_info.html',
                           user_id=user.user_id,
                           ratings=ratings,
                           age=age,
                           zipcode=zipcode)


@app.route('/movies')
def lists_movies():
    """Displays a list of all the movies."""

    movies = Movie.query.order_by('title').all()

    return render_template('movies.html', movies=movies)


@app.route('/movies/<int:movie_id>')
def movie_details(movie_id):
    """Displays movie details."""

    movie = Movie.query.get(movie_id)
    title = movie.title
    released_at = movie.released_at
    imdb_url = movie.imdb_url
    ratings = movie.ratings

    user_id = session.get('user_id')

    if user_id:
        user_rating = Rating.query.filter_by(movie_id=movie_id,
                                             user_id=user_id).first()
    else:
        user_rating = None

    #get average rating of movie
    rating_scores = [r.score for r in ratings]
    avg_rating = float(sum(rating_scores))/len(rating_scores)
    prediction = None

    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    return render_template("movie_info.html",
                           movie_id=movie.movie_id,
                           title=title,
                           released_at=released_at,
                           imdb_url=imdb_url,
                           average=avg_rating,
                           user_rating=user_rating,
                           prediction=int(prediction))


@app.route('/rate_movie', methods=['POST'])
def rate_movie():
    """Updates database with new rating."""

    #query database for existing rating by filtering by user_id/movie_id

    #User is adding a new rating
    rating = request.form.get('rating')
    movie_id = request.form.get('movie_id')
    user_id = request.form.get('user_id')

    #queries if user exists in database
    existing_rating = Rating.query.filter(Rating.user_id == user_id,
                                          Rating.movie_id == movie_id).first()
    #update existing rating, if true
    if existing_rating:
        existing_rating.score = rating
        flash("Rating updated.")
    else:
        new_rating = Rating(user_id=int(user_id),
                            movie_id=int(movie_id),
                            score=rating)

        flash("Rating added.")

        db.session.add(new_rating)

    db.session.commit()

    return redirect('/movies/{}'.format(movie_id))


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
