import json
import random
import re
import time
from pathlib import Path
from typing import Any, Union
import os

from queue import Queue
from web3 import Account, Web3

from app import config
from app.api_requests import make_action, cancel_action
from app.config import with_lock_quests, arbi_quests, fast_mint, separate_poly, to_withdraw_quests, pack_7_quests_names, \
    pack_7_name, pack_9_name, quix_name
from app.design import STRINGS, quests_choices
from app.logger import logger
from app.quests.quests_flow import quests
from app.utils import get_random_amount, uniswap_eth_usdc
from app.states import state


class QuestRunner:
    w3_opti = Web3(Web3.HTTPProvider(config.OPTIMISM_URL))
    usdc_address_opti = w3_opti.toChecksumAddress(config.USDC_OPTIMISM)
    usdc_opti = w3_opti.eth.contract(address=usdc_address_opti, abi=config.TOKEN_ABI)

    w3_arbi = Web3(Web3.HTTPProvider(config.ARBITRUM))
    usdc_address_arbi = w3_arbi.toChecksumAddress(config.USDC_ARBITRUM)
    usdc_arbi = w3_arbi.eth.contract(address=usdc_address_arbi, abi=config.TOKEN_ABI)

    quests_conf = {
        "stargate": [usdc_arbi, usdc_opti, round(random.uniform(101.2, 103.5), random.randint(3, 5))],
        "uni": [usdc_opti, get_random_amount(21.2, 22.5)],  # 2 swaps more than 20$ required
        "synapse": [usdc_opti, get_random_amount(21.2, 22.5)],
        "rubicon": [usdc_opti, get_random_amount(21.2, 22.5)],
        "velodrome": [usdc_opti, get_random_amount(27.2, 28.5)],
        "granary": [usdc_opti, get_random_amount(50.2, 51.2)],  # 30 deposit for opinion to get 22
        "perp": [usdc_opti, 101],
        "pika": [usdc_opti, True, get_random_amount(31.2, 32.5)],
        "pool_together": [usdc_opti, True, get_random_amount(21.2, 22.5)],
        "polynomial": [usdc_opti, True, get_random_amount(52.1, 52.7)],
        "quix": [usdc_opti, 0.0099]
    }

    def __init__(
            self,
            api_key: str,
            quests_to_run: str,
            file_name: str,
            min_wait_wlt: int,
            max_wait_wlt: int,
            min_wait_quest: int,
            max_wait_quest: int,
            type_of_running: str,
            window: Any
    ):
        """Голосование по указанным в ui данным."""
        self.api_key = api_key
        self.window = window
        self.quests_to_run = quests_to_run
        self.quests = {func.__name__: func for func in quests()}
        self.wallets = self.import_wallets(file_name)
        self.results = {}
        self.current_wallet = None
        self.type_of_running = type_of_running

        self.wallets_queue = Queue()
        for wallet in self.wallets:
            self.wallets_queue.put(wallet)

        self.wait_wlt = sorted((min_wait_wlt, max_wait_wlt))
        self.wait_quests = sorted((min_wait_quest, max_wait_quest))

    def do_work(self) -> Union[dict[Any, Any], Any]:
        pack_quests_choice = quests_choices[0]
        pack_7_choices = quests_choices[1]
        polynomial_choice = quests_choices[2]
        quix_choice = quests_choices[3]

        while (self.wallets_queue.qsize() or self.current_wallet is not None) and not state.get_state(PAUSE=True) and state.get_state(LIVE=True, index=0):
            if self.deposit():
                if len(self.quests_to_run) == 0:
                    self.current_wallet = None
                    logger.log(self.results)
                    return

                if pack_7_choices in self.quests_to_run:
                    if not self.current_wallet:
                        self.current_wallet = self.wallets_queue.get()
                        self.results[self.current_wallet.address] = {}

                        return self.window.stop_work()

                    if pack_7_choices in self.quests_to_run:
                        result_pack = self.run_pack_7_quests(self.current_wallet)
                        self.results[self.current_wallet.address][pack_7_name] = result_pack
                        if not result_pack:
                            logger.log("Something went wrong please try again ....")
                            return self.window.stop_work()

                    self.current_wallet = None
                else:
                    return self.window.stop_work()

                self.current_wallet = None
            else:
                wallet = self.wallets_queue.get()
                if pack_quests_choice in self.quests_to_run and polynomial_choice not in self.quests_to_run:
                    quests_to_run = with_lock_quests
                elif polynomial_choice in self.quests_to_run and pack_quests_choice not in self.quests_to_run:
                    quests_to_run = [separate_poly]
                else:
                    quests_to_run = to_withdraw_quests
                self.run_withdraw(wallet, quests_to_run)
            self.make_pause_btw_wlt()
        if len(self.results.keys()) > 0:
            logger.log(json.dumps(self.results))
        else:
            logger.log("Nothing results ....")

    def run_quest(self, wallet, quest_name: str, run_args=None):
        if not run_args:
            run_args = []
        args = [wallet] + run_args
        quest_flow = self.quests.get(quest_name)
        if quest_flow:
            return quest_flow(*args)

    def run_pack_quests(self, wallet):
        quests_to_run = self.get_final_quests_to_run()
        res = self.run_quests_loop_pack(arbi_quests, quests_to_run, wallet, self.quests_conf)
        if self.check_results_(res):
            # Run quests only if previous are passed
            order_to_fast_mint = random.sample(fast_mint, len(fast_mint))
            res = self.run_quests_loop_pack(order_to_fast_mint, quests_to_run, wallet, self.quests_conf)
            if self.check_results_(res):
                # Run quests only if previous are passed
                order_to_quests_with_lock = random.sample(with_lock_quests, len(with_lock_quests))
                res = self.run_quests_loop_pack(order_to_quests_with_lock, quests_to_run, wallet, self.quests_conf)
                if self.check_results_(res):
                    return True

    def check_usdc_balance_and_swap_if_need(self, wallet, usdc_need_to_min, usdc_need_to_max, offset=1):
        usdc_need_to = get_random_amount(usdc_need_to_min, usdc_need_to_max)
        usdc_balance = self.usdc_opti.functions.balanceOf(wallet.address).call()
        usdc_need = self.w3_opti.toWei(usdc_need_to, config.USDC_DECIMALS)
        if usdc_balance < usdc_need:
            need_more_usdc_wei = usdc_need - usdc_balance
            usdc_more = float(self.w3_opti.fromWei(need_more_usdc_wei, config.USDC_DECIMALS)) / 100 * (100 + offset)
            uniswap_eth_usdc(wallet, self.w3_opti, usdc_more)

    def run_pack_7_quests(self, wallet):
        self.check_usdc_balance_and_swap_if_need(wallet, config.USDC_AMOUNT_TO_7_PACK_MIN, config.USDC_AMOUNT_TO_7_PACK_MAX)
        quests_to_run = self.get_final_quests_to_run()
        order_to_pack_7 = random.sample(pack_7_quests_names, len(pack_7_quests_names))
        res = self.run_quests_loop_pack(order_to_pack_7, quests_to_run, wallet, self.quests_conf)
        if self.check_results_(res):
            arr = [config.separate_pika]
            res = self.run_quests_loop_pack(arr, quests_to_run, wallet, self.quests_conf)
            if self.check_results_(res):
                return True

    def set___d(self, data_to_run, to_run, key_run, api_action):
        if self.current_wallet:
            if not self.results.get(self.current_wallet.address):
                self.results[self.current_wallet.address] = {}
            if not self.results[self.current_wallet.address].get(key_run):
                success_pack, _id_pack = make_action(self.api_key, soft="optimism", type_=api_action)
                data_to_run[key_run]["success"] = success_pack
                data_to_run[key_run]["_id"] = _id_pack
                to_run[key_run] = {"success": success_pack, "result": _id_pack}
            else:
                to_run[key_run] = {"success": False}
        else:
            success_pack, _id_pack = make_action(self.api_key, soft="optimism", type_=api_action)
            data_to_run[key_run]["success"] = success_pack
            data_to_run[key_run]["_id"] = _id_pack
            to_run[key_run] = {"success": success_pack, "result": _id_pack}

    @staticmethod
    def check_results_(_results: dict):
        for _quest_name, result in _results.items():
            if not result:
                return False
        return True

    def run_polynomial(self, wallet):
        arr = [config.separate_poly]
        quests_to_run = self.get_final_quests_to_run()
        result = self.run_quests_loop_pack(arr, quests_to_run, wallet, self.quests_conf)
        if result.get(config.separate_poly):
            return True

    def run_quix(self, wallet):
        arr = [config.separate_quix]
        quests_to_run = self.get_final_quests_to_run()
        result = self.run_quests_loop_pack(arr, quests_to_run, wallet, self.quests_conf)
        if result.get(config.separate_quix):
            return True

    def run_withdraw(self, wallet, quests_to_run):
        order_to_quests_with_lock = random.sample(quests_to_run, len(quests_to_run))
        for to_withdraw_quest in order_to_quests_with_lock:
            quest_args = self.quests_conf[to_withdraw_quest]
            quest_args[1] = False
            self.run_quest(wallet, to_withdraw_quest, quest_args)
            self.make_pause_btw_quest()

    def run_quests_loop_pack(self, order, quests_to_run, wallet, array_of_functions):
        index = 0
        local_results = {}
        while index <= len(order) - 1 and not state.get_state(PAUSE=True) and state.get_state(LIVE=True, index=0):
            _quest = order[index]
            print(_quest)
            if _quest in quests_to_run and _quest in array_of_functions.keys():
                result = self.run_quest(wallet, _quest, array_of_functions[_quest])
                if not result:
                    logger.log(STRINGS[state.language]["log_return_points"] % _quest)
                    return {_quest: False}
                else:
                    local_results[_quest] = result
                self.make_pause_btw_quest()
            index += 1
        return local_results

    def get_final_quests_to_run(self):
        quests_to_run = []
        for pack_quests in self.quests_to_run:
            pack_quests_splitted = pack_quests.split(" ")
            for i in pack_quests_splitted:
                i_clear = re.sub("[^A-Za-z]", "", i)
                for j in config.all_config_tests:
                    j_clear = re.sub("[^A-Za-z]", "", i)
                    if i_clear.lower() == j_clear.lower() and j not in quests_to_run:
                        quests_to_run.append(j)
        return quests_to_run

    def import_wallets(self, file_name: str):
        accounts = []
        if os.path.exists(file_name):
            with Path(file_name).open() as file:
                for line in file.readlines():
                    key_ = line.replace("\n", "")
                    try:
                        acc = Account.from_key(key_)
                        accounts.append(acc)
                    except Exception as e:
                        logger.log(f"ERROR | Incorrect Private Key. Check format of the entered private key: {key_[0:int(len(key_)/2)]}...")
                        self.window.stop_work()
            if len(accounts) > 0:
                logger.log(STRINGS[state.language]["log_load_wlt"])
            return accounts
        else:
            logger.log(
                f"ERROR | Incorrect path to file with wallets! Tried upload from {file_name}")
            self.window.stop_work()
        return []


    def make_pause_btw_wlt(self) -> None:
        self.make_pause(self.wait_wlt)

    def make_pause_btw_quest(self) -> None:
        self.make_pause(self.wait_quests)

    @staticmethod
    def make_pause(wait_type):
        counter = random.randint(*wait_type)
        logger.log(STRINGS[state.language]["log_pause"].format(counter))
        step = 0.1
        while counter > 0 and not state.get_state(PAUSE=True) and state.get_state(LIVE=True, index=0):
            time.sleep(step)
            counter -= step

    def deposit(self):
        if self.type_of_running == STRINGS[state.language]["type_of_running"][0]:
            return True
        elif self.type_of_running == STRINGS[state.language]["type_of_running"][1]:
            return False
