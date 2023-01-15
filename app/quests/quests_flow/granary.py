from time import sleep

from eth_account.signers.local import LocalAccount
from web3 import Web3
from app.logger import logger

from app import config
from app.utils import call_function, approve, max_int, quest_log_str

RPC_URL = config.OPTIMISM_URL
w3 = Web3(Web3.HTTPProvider(RPC_URL))


op = w3.toChecksumAddress(config.OP)
lp_usdc_pool = w3.toChecksumAddress(config.GRANARY_USDC_LP)
borrowed_lp_address = w3.toChecksumAddress(config.GRANARY_BORROW_LP)
gas = 1_000_000


def granary(wallet: LocalAccount, usdc, amount_usdc_to_dep: int):
    logger.log(f"INFO | Granary | {quest_log_str} by wallet {wallet.address}")

    amount_to_depo_wei = w3.toWei(amount_usdc_to_dep, config.USDC_DECIMALS)
    amount_to_borrow_wei = w3.toWei(22, config.USDC_DECIMALS)  # 22 usdc_address
    lending_pool = w3.eth.contract(
        address=w3.toChecksumAddress(config.GRANARY_LENDING_POOL),
        abi=config.GRANARY_POOL_ABI
    )

    lp = w3.eth.contract(address=lp_usdc_pool, abi=config.GRANARY_USDC_LP_ABI)
    borrowed_lp = w3.eth.contract(address=borrowed_lp_address, abi=config.TOKEN_ABI)

    try:
        logger.log(f"INFO | Granary | Depositing into USDC pool .....\n")
        deposit_args = {
            "asset": usdc.address,
            "amount": amount_to_depo_wei,
            "onBehalfOf": wallet.address,
            "referralCode": 0
        }
        approve(w3, usdc, lending_pool.address, max_int, wallet)  # it's normal to approve for non-native
        call_function(lending_pool.functions.deposit, wallet, w3, args=deposit_args.values(), gas=gas)

        sleep(7)
        logger.log(f"INFO | Granary | Borrowing USDC .....")
        # borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf)
        borrow_args = {
            "asset": usdc.address,
            "amount": amount_to_borrow_wei,
            "interestRateMode": 2,
            "referralCode": 0,
            "onBehalfOf": wallet.address
        }
        call_function(lending_pool.functions.borrow, wallet, w3, args=borrow_args.values(), gas=gas)

        logger.log(f"INFO | Granary | Repaying USDC .....")
        # repay(address asset, uint256 amount, uint256 rateMode, address onBehalfOf)
        sleep(10)
        amount_to_repay = borrowed_lp.functions.balanceOf(wallet.address).call()
        repay_args = {
            "asset": usdc.address,
            "amount": amount_to_repay,
            "rateMode": 2,
            "onBehalfOf": wallet.address
        }
        approve(w3, usdc, lending_pool.address, max_int, wallet)
        call_function(lending_pool.functions.repay, wallet, w3, args=repay_args.values(), gas=gas)

        logger.log(f"INFO | Granary | Withdrawing USDC .....")
        # withdraw(address asset, uint256 amount, address to)
        sleep(7)
        balance_to_withdraw = lp.functions.getScaledUserBalanceAndSupply(wallet.address).call()[0]
        withdraw_args = {"asset": usdc.address, "amount": balance_to_withdraw, "to": wallet.address}
        approve(w3, lp, lending_pool.address, max_int, wallet)
        call_function(lending_pool.functions.withdraw, wallet, w3, args=withdraw_args.values(), gas=gas)
        return True
    except Exception as e:
        logger.log(f"ERROR | Granary | The error occured while swapping\n{e}")
