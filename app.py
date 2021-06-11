import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


#Home page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_books")
def get_books():
    books = mongo.db.books.find()
    return render_template("books.html", books=books)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome to All booked, {}".format(request.form.get("username")))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # session user's username from mongo db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


# Add a new book to db
@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        book = {
            "book_title": request.form.get("book_title"),
            "author": request.form.get("author"),
            "book_description": request.form.get("book_description"),
            "img_url": request.form.get("img_url"),
            "review": request.form.get("review"),
            "reviewed_by": session["user"]
        }
        mongo.db.books.insert_one(book)
        return redirect("/profile/<username>")


# allow user to see book
@app.route("/view_book/<book_title>")
def view_book(book_title):
    book = mongo.db.books.find_one({"_id": ObjectId(book_title)})
    return render_template("view_book.html", book=book)


# Users can edit book
@app.route("/edit_book/<book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    if request.method == "POST":
        edited_book = {
            "book_title": request.form.get("book_title"),
            "author": request.form.get("author"),
            "img_url": request.form.get("img_url"),
            "review": request.form.get("review"),
            "created_by": session["user"]
        }
        mongo.db.books.update({"_id": ObjectId(book_id)}, edited_book)

    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})
    return render_template("view_book.html", book=book)


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
