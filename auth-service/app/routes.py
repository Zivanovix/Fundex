from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import ROLE_EMPLOYEE, User

auth_bp = Blueprint("auth", __name__)

REGISTER_FIELDS = ["forename", "surname", "email", "password"]
LOGIN_FIELDS = ["email", "password"]


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    for field in REGISTER_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or len(value) == 0:
            return jsonify({"message": f"Field {field} is missing."}), 400

    forename = data["forename"]
    surname = data["surname"]
    email = data["email"]
    password = data["password"]

    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify({"message": "Invalid email."}), 400

    if len(password) < 8:
        return jsonify({"message": "Invalid password."}), 400

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"message": "Email already exists."}), 400

    user = User(
        forename=forename,
        surname=surname,
        email=email,
        password_hash=generate_password_hash(password),
        role=ROLE_EMPLOYEE,
    )
    db.session.add(user)
    db.session.commit()

    return "", 200


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    for field in LOGIN_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or len(value) == 0:
            return jsonify({"message": f"Field {field} is missing."}), 400

    email = data["email"]
    password = data["password"]

    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify({"message": "Invalid email."}), 400

    user = User.query.filter_by(email=email).first()
    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials."}), 400

    access_token = create_access_token(
        identity=user.email,
        additional_claims={
            "forename": user.forename,
            "surname": user.surname,
            "email": user.email,
            "role": user.role,
        },
    )

    return jsonify({"accessToken": access_token}), 200


@auth_bp.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    email = get_jwt_identity()

    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({"message": "Unknown user."}), 400

    db.session.delete(user)
    db.session.commit()

    return "", 200
