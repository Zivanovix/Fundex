from flask import Blueprint, current_app, jsonify

from app.auth import director_required
from app.orders import list_pending_orders

director_bp = Blueprint("director", __name__)


@director_bp.route("/pending_orders", methods=["GET"])
@director_required
def pending_orders():
    orders = list_pending_orders(current_app.redis)
    return jsonify({"orders": orders}), 200
