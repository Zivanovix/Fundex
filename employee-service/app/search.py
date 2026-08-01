from datetime import datetime


def _parse_iso_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _format_datetime(value):
    return value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{value.microsecond // 1000:03d}Z"


def build_query(data):
    conditions = []

    name = data.get("name")
    if name:
        conditions.append({"name": {"$regex": name}})

    category = data.get("category")
    if category:
        conditions.append({"categories": category})

    buying_date = data.get("buying_date")
    if buying_date:
        conditions.append({"buying_date": {"$gt": _parse_iso_datetime(buying_date)}})

    selling_date = data.get("selling_date")
    if selling_date:
        conditions.append({"selling_date": {"$lt": _parse_iso_datetime(selling_date)}})

    for info_filter in data.get("info_filters") or []:
        field = info_filter["field"]
        operator = info_filter["operator"]
        value = info_filter["value"]
        conditions.append({f"info.{field}": {f"${operator}": value}})

    if not conditions:
        return {}
    return {"$and": conditions}


def serialize_asset(doc):
    asset = {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "categories": doc["categories"],
        "buying_date": _format_datetime(doc["buying_date"]),
        "buying_price": doc["buying_price"],
        "info": doc.get("info", {}),
    }
    if "selling_date" in doc:
        asset["selling_date"] = _format_datetime(doc["selling_date"])
    if "selling_price" in doc:
        asset["selling_price"] = doc["selling_price"]
    return asset
