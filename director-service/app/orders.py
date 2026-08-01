import json


def list_pending_orders(redis_client):
    orders = []
    for key in redis_client.scan_iter(match="order:*"):
        value = redis_client.get(key)
        if value is not None:
            orders.append(json.loads(value))
    return orders
