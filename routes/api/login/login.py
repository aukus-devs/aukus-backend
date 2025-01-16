from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
)
from db_client.db_client import DatabaseClient

auth_bp = Blueprint("auth", __name__)
db = DatabaseClient()


def init_bcrypt(bcrypt_instance):
    global bcrypt
    bcrypt = bcrypt_instance


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        user = db.get_user_by_login(username=username)
        if user:
            is_valid = bcrypt.check_password_hash(user["password_hash"], password)
            if is_valid:
                session["username"] = user["username"]
                session["role"] = user["role"]
                return redirect("/")
            else:
                flash("Неверное имя пользователя или пароль. Попробуйте снова.")
        else:
            flash("Пользователь не найден или отключён")
    return render_template("login.html")
