from time import sleep

from eth_account.signers.local import LocalAccount
from web3 import Web3
from app.logger import logger

from app import config
from app.utils import call_function, approve, get_price, max_int, quest_log_str

RPC_URL = config.OPTIMISM_URL
w3 = Web3(Web3.HTTPProvider(RPC_URL))
op = w3.toChecksumAddress(config.OP)

# Long position params
isLong = True
executionFee = 25000
value_to_open = 0.00025
price_oracle_url = "https://api.bybit.com/v2/public/tickers"
price_request_params = {"symbol": "ETHUSDT"}
gas = 1_000_000


def pika(wallet: LocalAccount, usdc, deposit: bool = True, amount_usdc: int = 0):
    logger.log(f"INFO | Pika | {quest_log_str} by wallet {wallet.address}")

    position_manager = w3.eth.contract(
        address=w3.toChecksumAddress(config.PIKA_POSITION_MANAGER),
        abi=config.PIKA_POSITION_MANAGER_ABI
    )
    pika_router = w3.eth.contract(
        address=w3.toChecksumAddress(config.PIKA_PERP_V3),
        abi=config.PIKA_PERP_V3_ABI
    )

    if deposit:
        amount_to_use = w3.toWei(amount_usdc * 100, config.USDC_DECIMALS)
        try:
            logger.log(f"INFO | Pika | Set account manager to Pika Position Manager .....\n")
            set_acc_manager_args = {
                "manager": position_manager.address,
                "isActive": True,
            }
            approve(w3, usdc, position_manager.address, max_int, wallet)
            call_function(pika_router.functions.setAccountManager, wallet, w3, args=set_acc_manager_args.values(), gas=gas)

            logger.log(f"INFO | Pika | Creating OPEN long position .....")
            price = get_price(price_oracle_url, price_request_params)
            wei_price = w3.toWei(float(price) * 1.02 * 100, config.USDC_DECIMALS)  # for 2% more than the oracle price
            # createOpenPosition(uint256 _productId, uint256 _margin, uint256 _leverage, bool _isLong,
            #                    uint256 _acceptablePrice, uint256 _executionFee)

            open_long_args = {
                "_productId": 1,
                "_margin": amount_to_use,
                "_leverage": 100000000,  # 1x
                "_isLong": True,
                "_acceptablePrice": wei_price,
                "_executionFee": executionFee
            }
            approve(w3, usdc, position_manager.address, max_int, wallet)
            call_function(position_manager.functions.createOpenPosition, wallet, w3, args=open_long_args.values(),
                          value=value_to_open, gas=gas)

            logger.log(f"INFO | Pika | Creating CLOSE long position .....")
            # createClosePosition(uint256 _productId, uint256 _margin, bool _isLong, uint256 _acceptablePrice, uint256 _executionFee)
            price = get_price(price_oracle_url, price_request_params)
            wei_price = w3.toWei(float(price) * 0.98 * 100, config.USDC_DECIMALS)  # for 2% less than the oracle price
            close_long_args = {
                "_productId": 1,
                "_margin": amount_to_use,
                "_isLong": True,
                "_acceptablePrice": wei_price,
                "_executionFee": executionFee
            }
            call_function(position_manager.functions.createClosePosition, wallet, w3, args=close_long_args.values(),
                          value=value_to_open, gas=gas)

            logger.log(f"INFO | Pika | Staking {amount_usdc} USDC to vault for three days .....")
            sleep(15)
            approve(w3, usdc, pika_router.address, max_int, wallet)
            stake_args = {
                "amount": amount_to_use,
                "user": wallet.address,
            }
            call_function(pika_router.functions.stake, wallet, w3, args=stake_args.values(), gas=gas)
            return True
        except Exception as e:
            logger.log(f"ERROR | Pika | The error occured while swapping\n{e}")
    else:
        logger.log(f"INFO | Pika | Check LP balance before redeem .....\n")
        from web3.middleware import geth_poa_middleware
        try:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except:
            pass
        shares = pika_router.functions.getShare(wallet.address).call()

        sleep(2)
        if shares > 0:
            logger.log(f"INFO | Pika | Calculating redeem time .....")
            try:
                stake = pika_router.functions.getStake(wallet.address).call()
                user_timestamp = stake[-1]
                block_number = w3.eth.get_block_number()
                current_block = w3.eth.getBlock(block_number)
                block_time = current_block.timestamp
                timeDiff = block_time - user_timestamp
                prtocolVault = pika_router.functions.getVault().call()
                vault_staking_period = prtocolVault[4]
                if timeDiff > vault_staking_period:
                    logger.log(f"INFO | Pika | Redeem {amount_usdc} USDC to vault for three days .....")
                    redeem_args = {
                        "user": wallet.address,
                        "amount": shares,
                        "receiver": wallet.address,
                    }
                    call_function(pika_router.functions.redeem, wallet, w3, args=redeem_args.values(), gas=gas)
                    return True
                else:
                    logger.log(f"INFO | Pika | Not in time. Try again later")
                    return False
            except:
                logger.log(f"INFO | Pika | Can't get user stake\n")
        else:
            logger.log(f"INFO | Pika | Nothing to redeem\n")
            return False
