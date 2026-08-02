import uuid as uuid_module

from flask import Blueprint, current_app, jsonify, request

from app.assets import apply_order
from app.auth import director_required
from app.blockchain import build_vote_transactions, deploy_voting_contract, is_valid_address
from app.orders import (
    delete_order,
    get_order,
    list_pending_orders,
    save_contract_address,
)

director_bp = Blueprint("director", __name__)


def _is_valid_uuid(value):
    try:
        uuid_module.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


@director_bp.route("/pending_orders", methods=["GET"])
@director_required
def pending_orders():
    orders = list_pending_orders(current_app.redis)
    return jsonify({"orders": orders}), 200


@director_bp.route("/decision", methods=["POST"])
@director_required
def decision():
    data = request.get_json(silent=True) or {}

    order_uuid = data.get("uuid")
    if not isinstance(order_uuid, str) or len(order_uuid) == 0:
        return jsonify({"message": "Field uuid is missing."}), 400

    order = get_order(current_app.redis, order_uuid) if _is_valid_uuid(order_uuid) else None
    if order is None:
        return jsonify({"message": "Invalid uuid."}), 400

    if current_app.config["BLOCKCHAIN_ENABLED"]:
        return _start_voting(order_uuid, data)
    return _decide_immediately(order_uuid, order, data)


def _start_voting(order_uuid, data):
    """Deploys a voting contract; the listener applies the outcome later."""
    voters = data.get("voters")
    if not voters:
        return jsonify({"message": "Field voters is missing."}), 400

    if not all(is_valid_address(voter) for voter in voters):
        return jsonify({"message": "Invalid voter address."}), 400

    if len(voters) % 2 == 0:
        return jsonify({"message": "Even number of voters."}), 400

    address = deploy_voting_contract(current_app.web3, voters)
    save_contract_address(current_app.redis, order_uuid, address)

    approve_transaction, reject_transaction = build_vote_transactions(current_app.web3, address)
    return jsonify({
        "approve_transaction": approve_transaction,
        "reject_transaction": reject_transaction,
    }), 200


def _decide_immediately(order_uuid, order, data):
    approved = data.get("approved")
    if approved is None:
        return jsonify({"message": "Field approved is missing."}), 400

    if not isinstance(approved, bool):
        return jsonify({"message": "Invalid decision."}), 400

    delete_order(current_app.redis, order_uuid)

    if approved:
        apply_order(current_app.db, order)

    return "", 200


@director_bp.route("/report", methods=["GET"])
@director_required
def report():
    pipeline = [
        {"$unwind": "$categories"},
        {
            "$group": {
                "_id": "$categories",
                "spent": {"$sum": "$buying_price"},
                "earned": {"$sum": {"$ifNull": ["$selling_price", 0]}},
            }
        },
        {"$project": {"_id": 0, "category": "$_id", "spent": 1, "earned": 1}},
        {"$sort": {"earned": -1, "spent": 1, "category": 1}},
    ]
    statistics = list(current_app.db.assets.aggregate(pipeline))
    return jsonify({"statistics": statistics}), 200
