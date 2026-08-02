import json


def list_pending_orders(redis_client):
    orders = []
    for key in redis_client.scan_iter(match="order:*"):
        value = redis_client.get(key)
        if value is not None:
            orders.append(json.loads(value))
    return orders


def get_order(redis_client, order_uuid):
    value = redis_client.get(f"order:{order_uuid}")
    if value is None:
        return None
    return json.loads(value)


def delete_order(redis_client, order_uuid):
    redis_client.delete(f"order:{order_uuid}")


def save_contract_address(redis_client, order_uuid, address):
    redis_client.set(f"contract:{order_uuid}", address)


def delete_contract_address(redis_client, order_uuid):
    redis_client.delete(f"contract:{order_uuid}")


def list_deployed_contracts(redis_client):
    """Returns [(order_uuid, contract_address), ...] for all pending votes."""
    contracts = []
    for key in redis_client.scan_iter(match="contract:*"):
        address = redis_client.get(key)
        if address is not None:
            contracts.append((key.split(":", 1)[1], address))
    return contracts
