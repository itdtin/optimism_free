from eth_account.signers.local import LocalAccount
from web3 import Web3
from app.logger import logger
from time import sleep
from app import config
from app.utils import call_function, approve, get_price, max_int, quest_log_str

RPC_URL = config.OPTIMISM_URL
w3 = Web3(Web3.HTTPProvider(RPC_URL))

op = w3.toChecksumAddress(config.OP)
vETH_address = w3.toChecksumAddress("0x8C835DFaA34e2AE61775e80EE29E2c724c6AE2BB")

# Long position params
isLong = True
price_oracle_url = "https://api.bybit.com/v2/public/tickers"
price_request_params = {"symbol": "ETHUSDT"}
deposit_usdc = 15


def perp(wallet: LocalAccount, usdc, usdc_amount_to_deal: int = 101):
    logger.log(f"INFO | Perp | {quest_log_str} by wallet {wallet.address}")

    router = w3.eth.contract(
        address=w3.toChecksumAddress(config.PERP_ROUTER),
        abi=config.PERP_ROUTER_ABI
    )
    usdc_vault = w3.eth.contract(
        address=w3.toChecksumAddress(config.PERP_USDC_VAULT),
        abi=config.PERP_USDC_VAULT_ABI
    )

    try:
        logger.log(f"INFO | Perp | Depositing {deposit_usdc} usdc to cover commissions .....\n")
        amount_usdc_to_dep = w3.toWei(deposit_usdc, config.USDC_DECIMALS)
        deposit_args = {
            "token": usdc.address,
            "amount": amount_usdc_to_dep
        }
        approve(w3, usdc, usdc_vault.address, max_int, wallet)
        call_function(usdc_vault.functions.deposit, wallet, w3, args=deposit_args.values())
        sleep(3)
        price = get_price(price_oracle_url, price_request_params)
        eth_amount_to_deal = w3.toWei(usdc_amount_to_deal / float(price) * 0.98, config.ETH_DECIMALS)

        open_long_args = {
            "baseToken": vETH_address,
            "isBaseToQuote": False,
            "isExactInput": True,
            "amount": w3.toWei(usdc_amount_to_deal, config.ETH_DECIMALS),
            "oppositeAmountBound": eth_amount_to_deal,  # 1x
            "deadline": max_int,
            "sqrtPriceLimitX96": 0,
            "referralCode": "0x"
        }

        call_function(router.functions.openPosition, wallet, w3, args=[tuple(open_long_args.values())],  gas=1_500_000)
        sleep(3)
        close_long_args = {
            "address": vETH_address,
            "sqrtPriceLimitX96": 0,
            "oppositeAmountBound": w3.toWei(usdc_amount_to_deal * 0.95, config.ETH_DECIMALS),
            "deadline": max_int,
            "referralCode": "0x"
        }
        call_function(router.functions.closePosition, wallet, w3, args=[tuple(close_long_args.values())], gas=2_000_000)
        sleep(3)
        logger.log(f"INFO | Perp | Withdrawing all left usdc .....\n")
        withdraw_args = {
            "token": usdc.address,
        }
        call_function(usdc_vault.functions.withdrawAll, wallet, w3, args=withdraw_args.values(), gas=2_000_000)
        return True
    except Exception as e:
        logger.log(f"INFO | Perp | The error occured while swapping\n{e}")
