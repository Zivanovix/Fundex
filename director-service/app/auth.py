from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

DIRECTOR_ROLE = "director"


def director_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != DIRECTOR_ROLE:
            return jsonify({"msg": "Missing Authorization Header"}), 401
        return fn(*args, **kwargs)

    return wrapper
