from flask import Blueprint, current_app, jsonify, request

from app.auth import employee_required
from app.search import build_query, serialize_asset

employee_bp = Blueprint("employee", __name__)


@employee_bp.route("/search", methods=["POST"])
@employee_required
def search():
    data = request.get_json(silent=True) or {}
    query = build_query(data)
    assets = [serialize_asset(doc) for doc in current_app.db.assets.find(query)]
    return jsonify({"assets": assets}), 200
