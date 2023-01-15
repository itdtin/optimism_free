from datetime import datetime, timedelta
from time import sleep

from eth_account.signers.local import LocalAccount
from web3 import Web3
from app.logger import logger

from app import config
from app.utils import call_function, approve, max_int, quest_log_str

RPC_URL = config.OPTIMISM_URL
w3 = Web3(Web3.HTTPProvider(RPC_URL))


op = w3.toChecksumAddress(config.OP)
dai = w3.toChecksumAddress("0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1")  # for swap
velo = w3.toChecksumAddress("0x3c8B650257cFb5f272f799F5e2b4e65093a11a05")  # for swap
gas = 1_500_000


def velodrome(wallet: LocalAccount, usdc_token, usdc_amount: int):
    logger.log(f"INFO | Velodrome | {quest_log_str} by wallet {wallet.address}")
    router = w3.eth.contract(
        address=w3.toChecksumAddress(config.VELODROME_ROUTER),
        abi=config.VELODROME_ROUTER_ABI
    )
    rubicon_router = w3.eth.contract(
        address=w3.toChecksumAddress(config.RUBICON_ROUTER),
        abi=config.RUBICON_ROUTER_ABI
    )
    pair = w3.eth.contract(
        address=w3.toChecksumAddress(config.VELODROME_OP_USDC_PAIR),
        abi=config.VELODROME_PAIR_ABI
    )

    op_token = w3.eth.contract(address=op, abi=config.TOKEN_ABI)
    deadline = int(str((datetime.now() + timedelta(hours=4)).timestamp()).split(".")[0])

    try:
        logger.log(f"INFO | Velodrome | Swapping {usdc_amount/2} USDC -> OP .....\n")
        usdc_swap_wei = w3.toWei(usdc_amount/2, config.USDC_DECIMALS)
        swap_args = [
            usdc_swap_wei,
            0,
            [usdc_token.address, op],
            1
        ]
        approve(w3, usdc_token, rubicon_router.address, max_int, wallet)
        call_function(rubicon_router.functions.swap, wallet, w3, args=swap_args, gas=gas)
        sleep(10)

        op_balance_to_deposit = op_token.functions.balanceOf(wallet.address).call()
        usdc_balance_to_deposit = usdc_swap_wei
        logger.log(f"INFO | Velodrome | Adding liquidity into  OP {op_balance_to_deposit} -> USDC {usdc_balance_to_deposit} .....\n")
        add_liquidity_args = [
            op,
            usdc_token.address,
            False,
            op_balance_to_deposit,
            usdc_balance_to_deposit,
            0,
            0,
            wallet.address,
            deadline
        ]
        approve(w3, usdc_token, router.address, max_int, wallet)
        approve(w3, op_token, router.address, max_int, wallet)
        call_function(router.functions.addLiquidity, wallet, w3, args=add_liquidity_args, gas=gas)
        sleep(10)


        lp_balance = pair.functions.balanceOf(wallet.address).call()
        logger.log(f"INFO | Velodrome | Removing liquidity $OP---USDC - {lp_balance}")
        remove_args = [op, usdc_token.address, False, lp_balance, 0, 0, wallet.address, deadline]
        approve(w3, pair, router.address, max_int, wallet)
        call_function(router.functions.removeLiquidity, wallet, w3, args=remove_args, gas=gas)

        sleep(5)
        logger.log(f"INFO | Velodrome | Swap whole $OP ---> USDC")
        op_balance = op_token.functions.balanceOf(wallet.address).call()
        routes = [(op, velo, False), (velo, dai, False), (dai, usdc_token.address, False)]
        swap_args = [op_balance, 0, routes, wallet.address, deadline]
        approve(w3, op_token, router.address, max_int, wallet)
        call_function(router.functions.swapExactTokensForTokens, wallet, w3, args=swap_args, gas=gas)
        return True
    except Exception as e:
        logger.log(f"ERROR | Velodrome | The error occured while swapping\n{e}")
