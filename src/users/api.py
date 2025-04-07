from flask import Blueprint, request, session, redirect, flash, render_template
from src.users.queries import get_user_by_login
from src.core.extensions import bcrypt

users_bp = Blueprint("users", __name__)


@users_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        user = get_user_by_login(username)

        if user:
            is_valid = bcrypt.check_password_hash(user.password_hash, password)
            if is_valid:
                session["username"] = user.name
                session["role"] = user.role
                return redirect("/")
            else:
                flash("Неверное имя пользователя или пароль. Попробуйте снова.")
        else:
            flash("Пользователь не найден или отключён")

    return render_template("login.html")
