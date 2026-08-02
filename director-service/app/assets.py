from datetime import datetime, timezone

from bson import ObjectId


def apply_order(db, order):
    """Writes an approved order into MongoDB."""
    now = datetime.now(timezone.utc)
    if order["order_type"] == "BUY":
        db.assets.insert_one({
            "name": order["name"],
            "categories": order["categories"],
            "buying_price": order["buying_price"],
            "buying_date": now,
            "info": order["info"],
        })
    else:
        db.assets.update_one(
            {"_id": ObjectId(order["id"])},
            {"$set": {"selling_price": order["selling_price"], "selling_date": now}},
        )
