import re
import secrets
import sqlite3
import math

from flask import Flask, flash
from flask import g
from flask import abort, make_response, redirect, render_template, request, session
import markupsafe #mitigating injections

import config
import movies
import users

app = Flask(__name__)
app.secret_key = config.secret_key

#this function will check if the user is in session and is auhtorized to execute commands
def require_login():
    if "user_id" not in session:
        abort(403)

#this function will handle the csrf checks, while the csrf token is placed in html-file
def check_csrf():
    if "csrf_token" not in request.form:
        abort(403)
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

@app.template_filter()
def show_lines(content):
    #Here we sanitize the content. Escape replaces special characters and wraps safe for html
    #The function will save line breaks as well
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)

@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    page_size = 10
    movies_count = movies.movies_count()
    page_count = math.ceil(movies_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect("/1")
    if page > page_count:
        return redirect("/" + str(page_count))

    all_movies = movies.get_movies(page, page_size)
    return render_template("index.html", page=page, page_count=page_count, movies=all_movies)

@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:    #only users in database can be fetched, otherwise we call abort
        abort(404)
    user_movies = users.get_movies(user_id)
    return render_template("show_user.html", user=user, movies=user_movies)


@app.route("/movie/<int:movie_id>")
def show_movie(movie_id):
    movie = movies.get_movie(movie_id)
    if not movie:
        abort(404) #only movies in database can be fetched, otherwise we call abort
    return render_template("show_movie.html", movie=movie)

@app.route("/new_movie")
def new_movie():
    require_login() #only logged in users can add information
    return render_template("new_movie.html")

@app.route("/create_movie", methods=["POST"])
def create_movie():
    require_login() #only logged in users can add information
    check_csrf() #check the csrf token
    title = str(markupsafe.escape(request.form["title"])) # here we sanitize the content before posting to database
    if not title or len(title) > 100: 
        abort(403)
    user_id = session["user_id"]
    rating = request.form["rating"]
    if not rating:
        abort(403)
    movie_id = movies.add_movie(title, user_id, rating)
    return redirect("/movie/" + str(movie_id))

@app.route("/edit_movie/<int:movie_id>")
def edit_movie(movie_id):
    require_login() #only logged in users can edit information
    movie = movies.get_movie(movie_id)
    if not movie:
        abort(404)
    if movie["user_id"] != session["user_id"]: #here we check the user can only edit their own input --> authorization
        abort(403)

    return render_template("edit_movie.html", movie=movie)

@app.route("/update_movie", methods=["POST"])
def update_movie():
    check_csrf() #csrf token check
    movie_id = request.form["movie_id"]
    movie = movies.get_movie(movie_id)
    if not movie: #checking that movie exists
        abort(404)
    if movie["user_id"] != session["user_id"]:
        abort(403)
    title = str(markupsafe.escape(request.form["title"])) # here we sanitize the content before posting to database
    if not title or len(title) > 100: #limit the input
        abort(403)
    rating = request.form["rating"]
    if not rating:
        abort(403)
    movies.update_movie(movie_id, title, rating)
    return redirect("/movie/" + str(movie_id))

@app.route("/remove_movie/<int:movie_id>", methods=["GET", "POST"])
def remove_movie(movie_id):
    require_login() #only logged in users can remove information
    movie = movies.get_movie(movie_id)
    if not movie:
        abort(404)
    #here we check the user can only edit their own input --> authorization
    if movie["user_id"] != session["user_id"]:
        abort(403)
    if request.method == "GET":
        return render_template("remove_movie.html", movie=movie)
    if request.method == "POST":
        if "remove" in request.form:
            check_csrf() #check the csrf token
            movies.remove_movie(movie_id)
            return redirect("/")
        return redirect("/movie/" + str(movie_id))
    

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    if not username or len(username) > 50:
        flash("ERROR: username is empty or too long")
        return redirect("/register")
    password1 = request.form["password1"]
    
    #here we check that the password is strong enough
    if not password1 or len(password1) < 8 or len(password1) > 50:
        flash("ERROR: password does not fill the requirements")
        return redirect("/register")
    
    digit = re.search(r"\d", password1) is None
    uppercase = re.search(r"[A-Z]", password1) is None
    lowercase = re.search(r"[a-z]", password1) is None
    symbol = re.search(r"[ !#$%&'()*+,-./\[]^_`{}~"+r'"]', password1) is None

    if digit or uppercase or lowercase or symbol:
        flash("ERROR: password does not fill the requirements")
        return redirect("/register")

    password2 = request.form["password2"]
    if password1 != password2:
        flash("ERROR: passwords do not match")
        return redirect("/register")

    try:
        users.create_user(username, password1)
    except sqlite3.IntegrityError:
        flash("ERROR: username is taken")
        return redirect("/register")

    flash("User created")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", username="")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_id = users.check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            session["csrf_token"] = secrets.token_hex(16) #here we create a csrf session token
            return redirect("/")
        flash("ERROR: wrong username or password")
        return render_template("login.html", username=username)

@app.route("/logout")
def logout():
    if "user_id" in session:
        del session["user_id"] #delete the session information
        del session["username"] #delete the session information
    return redirect("/")
