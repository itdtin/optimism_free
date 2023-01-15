from time import sleep

from eth_account.signers.local import LocalAccount
from web3 import Web3
from app.logger import logger

from app import config
from app.utils import quest_log_str, approve, call_function, max_int

RPC_URL = config.OPTIMISM_URL
w3 = Web3(Web3.HTTPProvider(RPC_URL))


eth = w3.toChecksumAddress(config.ETH)
usdt_address = w3.toChecksumAddress("0x94b008aa00579c1307b0ef2c499ad98a8ce58e58")
usdc_usdt_pool = w3.toChecksumAddress("0xF1F199342687A7d78bCC16fce79fa2665EF870E1")


def uni(wallet: LocalAccount, usdc, amount_usdc: int):
    logger.log(f"INFO | Uniswap | {quest_log_str} by wallet {wallet.address}")

    usdt = w3.eth.contract(
            address=w3.toChecksumAddress(usdt_address),
            abi=config.TOKEN_ABI
        )

    uniswap_router = w3.eth.contract(
        address=w3.toChecksumAddress(config.UNISWAP_ROUTER_V3),
        abi=config.UNI_ROUTER_ABI
    )

    try:
        logger.log(f"INFO | Uniswap | Swapping USDC -> USDT .....\n")
        exactInputSingleParams = {
            "tokenIn": usdc.address,
            "tokenOut": usdt.address,
            "fee": 100,
            "recipient": wallet.address,
            "amountIn": w3.toWei(amount_usdc, config.USDC_DECIMALS),
            "amountOutMinimum": 0,
            "sqrtPriceLimitX96": 0
        }
        approve(w3, usdc, uniswap_router.address, max_int, wallet)
        call_function(uniswap_router.functions.exactInputSingle, wallet, w3, args=[tuple(exactInputSingleParams.values())])

        sleep(10)
        logger.log(f"INFO | Uniswap | Swapping USDT -> USDC .....\n")
        balance_usdt_to_swap = usdt.functions.balanceOf(wallet.address).call()
        exactInputSingleParams = {
            "tokenIn": usdt.address,
            "tokenOut": usdc.address,
            "fee": 100,
            "recipient": wallet.address,
            "amountIn": balance_usdt_to_swap,
            "amountOutMinimum": 0,
            "sqrtPriceLimitX96": 0
        }
        approve(w3, usdt, uniswap_router.address, max_int, wallet)
        call_function(uniswap_router.functions.exactInputSingle, wallet, w3, args=[tuple(exactInputSingleParams.values())])
        return True
    except Exception as e:
        logger.log(f"ERROR | Uniswap | The error occured while swapping\n{e}")
