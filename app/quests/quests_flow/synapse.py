from datetime import datetime, timedelta
from time import sleep

from eth_account.signers.local import LocalAccount
from web3 import Web3
from app.logger import logger
from web3.contract import Contract

from app import config
from app.utils import approve, call_function, max_int, quest_log_str

RPC_URL = config.OPTIMISM_URL
w3 = Web3(Web3.HTTPProvider(RPC_URL))


lp_address = w3.toChecksumAddress("0x2c6d91accC5Aa38c84653F28A80AEC69325BDd12")  # nusd
eth = w3.toChecksumAddress(config.ETH)


def synapse(wallet: LocalAccount, usdc, amount_usdc: int):
    logger.log(f"INFO | Synapse | {quest_log_str} by wallet {wallet.address}")
    lp_token = w3.eth.contract(address=lp_address, abi=config.TOKEN_ABI)
    synapse_pool_contract = w3.eth.contract(
        address=w3.toChecksumAddress(config.SYNAPSE_POOL),
        abi=config.SYNAPSE_POOL_ABI
    )

    add_liquidity(wallet, usdc, synapse_pool_contract, amount_usdc)
    sleep(10)
    remove_liquidity(wallet, lp_token, synapse_pool_contract)
    return True


def add_liquidity(wallet: LocalAccount, usdc: Contract, synapse_pool_contract, amount: int or float):
    deadline = int(str((datetime.now() + timedelta(hours=4)).timestamp()).split(".")[0])
    approve(w3, usdc, synapse_pool_contract.address, max_int, wallet)

    txObj = {
        "amounts": [0, w3.toWei(amount, config.USDC_DECIMALS)],
        "minMintAmount": 0,
        "deadline": deadline
    }
    call_function(synapse_pool_contract.functions.addLiquidity, wallet, w3, 0, 1_000_000, txObj.values())


def remove_liquidity(wallet: LocalAccount, lp_token: Contract, synapse_pool_contract):
    token_index = 1
    deadline = int(str((datetime.now() + timedelta(hours=4)).timestamp()).split(".")[0])
    sleep(5)
    lp_balance = lp_token.functions.balanceOf(wallet.address).call()
    approve(w3, lp_token, synapse_pool_contract.address, max_int, wallet)
    usdc_to_remove = synapse_pool_contract.functions.calculateRemoveLiquidityOneToken(lp_balance, token_index).call()
    sleep(2)
    usdc_to_remove = int(usdc_to_remove * 0.98)  # to be sure
    txObj = {
        "amount": lp_balance,
        "tokenIndex": token_index,
        "minAmount": usdc_to_remove,
        "deadline": deadline
    }
    call_function(synapse_pool_contract.functions.removeLiquidityOneToken, wallet, w3, 0, 1_000_000, txObj.values())


