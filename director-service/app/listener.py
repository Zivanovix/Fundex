import threading
import time
import traceback

from app.assets import apply_order
from app.blockchain import read_voting_result
from app.orders import delete_contract_address, delete_order, get_order, list_deployed_contracts

POLL_INTERVAL_SECONDS = 2


def process_finished_votes(db, redis_client, web3):
    """Applies and clears every deployed contract whose voting has concluded."""
    for order_uuid, address in list_deployed_contracts(redis_client):
        finished, approved = read_voting_result(web3, address)
        if not finished:
            continue

        if approved:
            order = get_order(redis_client, order_uuid)
            if order is not None:
                apply_order(db, order)

        delete_order(redis_client, order_uuid)
        delete_contract_address(redis_client, order_uuid)


def run_listener(db, redis_client, web3):
    while True:
        try:
            process_finished_votes(db, redis_client, web3)
        except Exception:
            traceback.print_exc()
        time.sleep(POLL_INTERVAL_SECONDS)


def start_listener(db, redis_client, web3):
    thread = threading.Thread(
        target=run_listener,
        args=(db, redis_client, web3),
        daemon=True,
    )
    thread.start()
    return thread
