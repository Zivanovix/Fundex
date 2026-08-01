import json
import uuid as uuid_module


def save_buy_order(redis_client, name, categories, buying_price, info):
    order_uuid = str(uuid_module.uuid4())
    order = {
        "uuid": order_uuid,
        "order_type": "BUY",
        "name": name,
        "categories": categories,
        "info": info,
        "buying_price": buying_price,
    }
    redis_client.set(f"order:{order_uuid}", json.dumps(order))
    return order_uuid


def save_sell_order(redis_client, asset_id, selling_price):
    order_uuid = str(uuid_module.uuid4())
    order = {
        "uuid": order_uuid,
        "order_type": "SELL",
        "id": asset_id,
        "selling_price": selling_price,
    }
    redis_client.set(f"order:{order_uuid}", json.dumps(order))
    return order_uuid
