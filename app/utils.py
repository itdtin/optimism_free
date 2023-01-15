import random
import time
from pathlib import Path
from time import sleep
from urllib.parse import urlparse

import requests
from eth_account.signers.local import LocalAccount
from app.logger import logger
from web3 import Account, Web3

import app.config as config
from app.states import state

max_int = 115792089237316195423570985008687907853269984665640564039457584007913129639935
quest_log_str = "Started"


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        else:
            cls._instances[cls].__init__(*args, **kwargs)
        return cls._instances[cls]


def approve(web3: Web3, token, spender, amount, wallet: LocalAccount, gas=700_000):
    return call_function(token.functions.approve, wallet, web3, args=[spender, amount], gas=gas)


def call_function(function, wallet: LocalAccount, w3: Web3, value=0, gas: int = 1_500_000, args=None):
    if args is None:
        args = []
    tryNum = 0
    while True and not state.get_state(PAUSE=True) and state.get_state(LIVE=True, index=0):
        dict_transaction = {
            "chainId": w3.eth.chain_id,
            "from": wallet.address,
            "value": w3.toWei(value, config.ETH_DECIMALS),
            "gas": gas,
            "gasPrice": w3.eth.gas_price,
            "nonce": w3.eth.getTransactionCount(wallet.address),
        }
        logger.log(f"INFO | Calling {function.fn_name} .... attempt {tryNum + 1}")
        try:
            transaction = function(*args).buildTransaction(dict_transaction)
            signed_txn = wallet.sign_transaction(transaction)

            txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            sleep(random.randint(random.randint(8, 10), random.randint(17, 20)))
            receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
            sleep(random.randint(random.randint(5, 12), random.randint(13, 20)))

            if receipt.status != 1:
                raise Exception("Failed Tx")
            logger.log(f"INFO | Successful called function {function.fn_name}\n {txn_hash.hex()}")
            return receipt
        except Exception as e:
            tryNum += 1
            logger.log(f"ERROR | while calling {function.fn_name}.\n{e}")
            if tryNum > config.ATTEMTS_TO_NODE_REQUEST:
                logger.log(f"ERROR | while calling {function.fn_name}.\n{e}\n STOP QUEST")
                raise e
            sleep(15)


def get_price(url, params):
    for i in range(1, 4):
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()['result'][0]["last_price"]


def eth_price():
    while True:
        try:
            r = requests.get('https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD')
            return r.json()['USD']
        except Exception as e:
            logger.log(f'ERROR | {e}')
            time.sleep(15)


def load_wallets():
    file = Path("../wallets.txt").open()
    return [Account.from_key(line.replace("\n", "")) for line in file.readlines()]


def uniswap_eth_usdc(wallet, w3, usdc_need, offset=3):
    price = eth_price()
    amount_eth_to_swap = usdc_need / price / 100 * (100 + offset)
    amount_eth_to_swap_wei = w3.toWei(amount_eth_to_swap, config.ETH_DECIMALS)
    usdc_amount_wei = w3.toWei(usdc_need, config.USDC_DECIMALS)
    logger.log(f"Swapping {amount_eth_to_swap} ETH to USDC ...")
    uniswap_router = w3.eth.contract(
        address=w3.toChecksumAddress(config.UNISWAP_ROUTER_V3),
        abi=config.UNI_ROUTER_ABI
    )
    swapParams = (
        w3.toChecksumAddress(config.WETH),
        w3.toChecksumAddress(config.USDC_OPTIMISM),
        500,
        wallet.address,
        usdc_amount_wei,
        amount_eth_to_swap_wei,
        0
    )
    encoded_swap = uniswap_router.encodeABI("exactOutputSingle", [swapParams])
    encoded_refund = uniswap_router.encodeABI("refundETH", [])

    deadline = max_int
    call_function(uniswap_router.functions.multicall, wallet, w3, value=amount_eth_to_swap,
                  args=[deadline, [encoded_swap, encoded_refund]], gas=3_000_000)
    return True


def get_swap_data(tokenFrom, tokenTo, fromAddress, amount):
    params = {
        'fromTokenAddress': tokenFrom,
        'toTokenAddress': tokenTo,
        'amount': amount,
        'fromAddress': fromAddress,
        'slippage': '3',
        'disableEstimate': 'true'
    }

    while True:
        try:
            response = requests.get('https://api.1inch.io/v4.0/10/swap', params=params)
            return (response.json())['tx']['data']
        except Exception as e:
            logger.log(f'ERROR | {e}')
            time.sleep(15)


def get_with_headers(url, headers):
    tryNum = 0
    while True:
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            tryNum += 1
            if tryNum > config.ATTEMTS_TO_API_REQUEST:
                logger.log(f"ERROR | Can't get response from {url}.\n{e}\n STOP QUEST")
                raise e
            sleep(10)


def get_random_amount(_min, _max, digitMin=3, digitMax=5):
    return round(random.uniform(_min, _max), random.randint(digitMin, digitMax))


def decode_hex(hexStr):
    # Trim '0x' from beginning of string
    hexdataTrimed = hexStr[2:]
    # Split trimmed string every 64 characters
    n = 64
    dataSplit = [hexdataTrimed[i:i + n] for i in range(0, len(hexdataTrimed), n)]
    # Fill new list with converted decimal values
    data = []
    for val in range(len(dataSplit)):
        toDec = int(dataSplit[val], 16)
        data.append(toDec)
    return data


def decodeTx(tx_hash, w3, contract):
    tx = w3.eth.get_transaction(tx_hash)
    encoded_tx = contract.decode_function_input(tx.input)
    return encoded_tx


def fill_order(w3, order_json):
    """fulfillOrder(Order calldata order, bytes32 fulfillerConduitKey) QUIX"""
    params = order_json["parameters"]
    offerer = w3.toChecksumAddress(params["offerer"])
    zone = w3.toChecksumAddress(params["zone"])
    offer_items = []
    for i in params["offer"]:
        offer_items.append((i["itemType"], w3.toChecksumAddress(i["token"]), int(i["identifierOrCriteria"]),
                            int(i["startAmount"]), int(i["endAmount"])))
    consideration_items = []
    for item in params["consideration"]:
        consideration_items.append((item["itemType"], w3.toChecksumAddress(item["token"]),
                                    int(item["identifierOrCriteria"]), int(item["startAmount"]), int(item["endAmount"]),
                                    w3.toChecksumAddress(item["recipient"])))
    order_type = int(params["orderType"])
    start_time = int(params["startTime"])
    end_time = int(params["endTime"])
    zone_hash = w3.toBytes(hexstr=params["zoneHash"])  # bytes32
    salt = decode_hex(params["salt"])[0]
    conduit_key = w3.toBytes(hexstr=params["conduitKey"])  # bytes32
    total_consideration = params["totalOriginalConsiderationItems"]

    order_params = (
        offerer,
        zone,
        offer_items,
        consideration_items,
        order_type,
        start_time,
        end_time,
        zone_hash,
        salt,
        conduit_key,
        total_consideration
    )
    return order_params
