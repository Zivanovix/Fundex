from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request

from app.auth import employee_required
from app.orders import save_buy_order, save_sell_order
from app.search import build_query, serialize_asset

employee_bp = Blueprint("employee", __name__)


@employee_bp.route("/search", methods=["POST"])
@employee_required
def search():
    data = request.get_json(silent=True) or {}
    query = build_query(data)
    assets = [serialize_asset(doc) for doc in current_app.db.assets.find(query)]
    return jsonify({"assets": assets}), 200


@employee_bp.route("/create_buy_order", methods=["POST"])
@employee_required
def create_buy_order():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    if not isinstance(name, str) or len(name) == 0:
        return jsonify({"message": "Field name is missing."}), 400

    categories = data.get("categories")
    if categories is None:
        return jsonify({"message": "Field categories is missing."}), 400

    buying_price = data.get("buying_price")
    if buying_price is None:
        return jsonify({"message": "Field buying_price is missing."}), 400

    info = data.get("info")
    if info is None:
        return jsonify({"message": "Field info is missing."}), 400

    if len(categories) == 0:
        return jsonify({"message": "Categories list is empty."}), 400

    if isinstance(buying_price, bool) or not isinstance(buying_price, (int, float)) or buying_price <= 0:
        return jsonify({"message": "Invalid buying price."}), 400

    save_buy_order(current_app.redis, name, categories, buying_price, info)

    return "", 200


@employee_bp.route("/create_sell_order", methods=["POST"])
@employee_required
def create_sell_order():
    data = request.get_json(silent=True) or {}

    asset_id = data.get("id")
    if not isinstance(asset_id, str) or len(asset_id) == 0:
        return jsonify({"message": "Field id is missing."}), 400

    selling_price = data.get("selling_price")
    if selling_price is None:
        return jsonify({"message": "Field selling_price is missing."}), 400

    if not ObjectId.is_valid(asset_id) or current_app.db.assets.find_one({"_id": ObjectId(asset_id)}) is None:
        return jsonify({"message": "Invalid id."}), 400

    if isinstance(selling_price, bool) or not isinstance(selling_price, (int, float)) or selling_price <= 0:
        return jsonify({"message": "Invalid selling price."}), 400

    save_sell_order(current_app.redis, asset_id, selling_price)

    return "", 200
