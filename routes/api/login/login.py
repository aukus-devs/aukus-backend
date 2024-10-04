from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
)
from db_client.db_client import DatabaseClient

auth_bp = Blueprint("auth", __name__)
db = DatabaseClient()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.get_user_by_logpass(username=username, password=password)

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect("/")
        else:
            return jsonify(
                {"error": "Неверное имя пользователя или пароль. Попробуйте снова."}
            )

    return render_template("login.html")
