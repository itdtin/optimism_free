from hashlib import sha256

import requests

base_url = "http://82.180.139.32:8001/api/"


def get_balance(api_key) -> int:
    """Проверка баланса."""

    url = base_url + f"{api_key}/get_userinfo"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()["balance"]
    else:
        return 0


def make_action(api_key, soft, type_):
    """Проверка на совершение действия."""
    try:
        url = base_url + f"{api_key}/new_action"
        data = {"soft": soft, "action": type_}
        resp = requests.post(url, data=data).json()
        if resp["success"]:
            return resp["success"], resp["cancel_id"]
        elif not resp["success"] and resp["error"]:
            return resp["success"], resp["error"]
        else:
            return resp["success"], 0
    except Exception as e:
        return False, f"{e}"


def cancel_action(api_key, _id: int) -> None:
    """Возврат поинтов за неуспешное действие."""
    url = base_url + f"{api_key}/cancel_action"
    _hash = sha256(
        f"{api_key},{_id},6PoEoBzHk7mCn".encode()).hexdigest()
    requests.post(url, data={"id": _id, "hash": _hash})
