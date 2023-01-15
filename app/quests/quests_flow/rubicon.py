from time import sleep

from eth_account.signers.local import LocalAccount
from web3 import Web3
from app.logger import logger

from app import config
from app.utils import call_function, approve, max_int, quest_log_str

RPC_URL = config.OPTIMISM_URL
w3 = Web3(Web3.HTTPProvider(RPC_URL))


op = w3.toChecksumAddress(config.OP)
op_pool_lp_token = w3.toChecksumAddress("0x574a21fE5ea9666DbCA804C9d69d8Caf21d5322b")
gas = 2_000_000


def rubicon(wallet: LocalAccount, usdc_token, amount_usdc: int):
    logger.log(f"INFO | Rubicon | {quest_log_str} by wallet {wallet.address}")
    router = w3.eth.contract(
        address=w3.toChecksumAddress(config.RUBICON_ROUTER),
        abi=config.RUBICON_ROUTER_ABI
    )
    pool = w3.eth.contract(
        address=w3.toChecksumAddress(config.RUBICON_OP_POOL),
        abi=config.RUBICON_POOL_ABI
    )

    op_token = w3.eth.contract(address=op, abi=config.TOKEN_ABI)

    try:
        logger.log(f"INFO | Rubicon | Swapping {amount_usdc} USDC -> OP .....\n")
        usdc_swap_wei = w3.toWei(amount_usdc, config.USDC_DECIMALS)
        swap_args = [
            usdc_swap_wei,
            0,
            [usdc_token.address, op],
            1
        ]
        approve(w3, usdc_token, router.address, max_int, wallet)
        call_function(router.functions.swap, wallet, w3, args=swap_args, gas=gas)

        sleep(6)

        op_balance_after_swap = op_token.functions.balanceOf(wallet.address).call()
        logger.log(f"INFO | Rubicon | Depositing into pool $OP - {op_balance_after_swap}")
        deposit_args = [op_balance_after_swap]
        approve(w3, op_token, pool.address, max_int, wallet)
        call_function(pool.functions.deposit, wallet, w3, args=deposit_args, gas=gas)

        lp_token = w3.eth.contract(address=op_pool_lp_token, abi=config.TOKEN_ABI)
        sleep(7)

        lp_balance = lp_token.functions.balanceOf(wallet.address).call()
        logger.log(f"INFO | Rubicon | Exit pool $OP - {lp_balance}")
        exit_pool_args = [lp_balance]
        approve(w3, lp_token, pool.address, max_int, wallet)
        call_function(pool.functions.withdraw, wallet, w3, args=exit_pool_args, gas=gas)
        sleep(5)

        logger.log(f"INFO | Rubicon | Swapping OP -> USDC .....\n")
        op_swap_wei = op_token.functions.balanceOf(wallet.address).call()
        swap_args = [
            int(op_swap_wei * 0.99),
            0,
            [op, usdc_token.address],
            1
        ]
        approve(w3, op_token, router.address, max_int, wallet)
        call_function(router.functions.swap, wallet, w3, args=swap_args, gas=gas)
        return True
    except Exception as e:
        logger.log(f"ERROR | Rubicon |The error occured while swapping\n{e}")
