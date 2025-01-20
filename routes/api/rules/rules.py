from functools import wraps
from flask import Blueprint, request, jsonify, session, Response
from db_client.db_client import DatabaseClient
import json
import logging

rules_bp = Blueprint("rules", __name__)
db = DatabaseClient()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session and "role" not in session:
            return jsonify({"error": f"Auth required"}), 401
        return f(*args, **kwargs)

    return decorated_function


def available_for_roles(roles=None):
    if roles is None:
        roles = ["player", "moder", "admin"]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "username" not in session and "role" not in session:
                return jsonify({"error": f"Auth required"}), 401
            if session["role"] not in roles:
                return jsonify({"error": f"Forbidden"}), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator


@rules_bp.route("/api/rules", methods=["POST"])
@login_required
@available_for_roles(["admin", "player"])
def insert_rules():
    data = request.get_json()
    required_fields = ["rule_data"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        rule_data = data["rule_data"]
        db.insert_rules(rule_data)
        return jsonify({"message": "Rules insert successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rules_bp.route("/api/rules", methods=["GET"])
def get_rules():
    try:
        rule = db.get_rules()[0]
        result = {
            "rules_data": rule["rules_data"],
            "version": str(rule["version"]),
            "id": rule["id"],
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rules_bp.route("/api/rules/all", methods=["GET"])
def get_all_rules():
    try:
        rules = db.get_rules(all=True)
        result = [
            {
                "rules_data": rule["rules_data"],
                "version": str(rule["version"]),
                "id": rule["id"],
            }
            for rule in rules
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
