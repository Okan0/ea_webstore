"""
This module provides a LotRWebstoreConnector class for interacting
with the Lord of the Rings - Heroes of Middleearth web store.

It allows users to request one-time codes, verify codes, retrieve offers,
and purchase items from the store.
"""

import logging
import os
import pickle
import re
from datetime import datetime, timedelta
from sched import scheduler
from time import sleep, time
from typing import Optional, Union
from uuid import uuid4

from requests import ConnectionError as RequestConnectionError
from requests import Session
from requests import Timeout as RequestTimeout

from core.config import Config
from core.utils import slugify
from gmail.connector import GmailConnector
from webstore.lotr.types import StoreData

# TODO: Move scheduler logic to own class
# TODO: Update and add docstrings

class LotRWebstoreConnector:
    """
    A class for connecting to and interacting with the
    Lord of the Rings - Heroes of Middleearth web store.

    Args:
        email (str): The email associated with the user's account.

    This class provides methods for requesting one-time codes (OTC),
    verifying codes, retrieving offers, and purchasing items from the web store.
    """

    BASE_URL = "https://store.lotr-home.ea.com"
    EA_SUBJECT_PATTERN = re.compile("^Verification Code For EA[^0-9]*([0-9]+)$")
    logger = logging.getLogger("LotRWebstoreConnector")

    def __init__(self, email: str, config: Optional[Union[str, Config]] = None):
        self.config: Config = Config.load_config(config) or Config.get_global_config()
        self.email: str = email
        self.gmail_connector: GmailConnector = GmailConnector(
            email=email, config=self.config
        )
        self.session_filename: str = os.path.join(
            self.config.webstore_sessions_location,
            f"lotr_{slugify(email)}_session.pickle",
        )
        self.session: Session = Session()
        self.scheduler = scheduler(time, sleep)
        self.default_headers = {"Accept-Language": "DE"}
        self.logger.setLevel(self.config.lotr_webstore_log_level)

        # Attempt to load the session from a file
        if os.path.exists(self.session_filename):
            self.load_session()

        self.schedule_ping()
        self.schedule_connection_check()

    def load_session(self):
        """
        Load and deserialize a session object from a file.
        """
        with open(self.session_filename, "rb") as file:
            self.session = pickle.load(file)
        self.logger.info(
            "Successfully loaded session from file '%s'", self.session_filename
        )

    def save_session(self):
        """
        Serialize and save the session object to a file.
        """
        with open(self.session_filename, "wb") as file:
            pickle.dump(self.session, file)
        self.logger.info(
            "Successfully saved session to file '%s'", self.session_filename
        )

    def request_otc(self):
        """
        Request a one-time code (OTC) for authentication.

        Raises:
            NotImplementedError: If the request returns an unhandled status code.

        This method sends a request to obtain a one-time code for authentication.
        """
        response = self.session.post(
            url=f"{self.BASE_URL}/auth/request_otc",
            headers=self.default_headers,
            json={"email": self.email},
        )
        self.logger.debug(
            "[request_otc - %s] Request Body: %s",
            self.email,
            str(response.request.body),
        )
        self.logger.debug(
            "[request_otc - %s] Response Status Code: %i",
            self.email,
            response.status_code,
        )
        self.logger.debug(
            "[request_otc - %s] Response Body: %s", self.email, response.text
        )
        if response.status_code != 200:
            raise NotImplementedError(f'Unhandled Status Code "{response.status_code}"')

    def verify_otc(self, code: str):
        """
        Verify the one-time code (OTC) for authentication.

        Args:
            code (str): The one-time code to verify.

        Raises:
            NotImplementedError: If the request returns an unhandled status code.

        This method sends a request to verify the provided one-time code for authentication.
        If the verification is successful, the session is updated, and the session state is saved to a file.
        """
        response = self.session.post(
            url=f"{self.BASE_URL}/auth/code_check",
            headers=self.default_headers,
            json={
                "email": self.email,
                "code": code,
                "rememberMe": True,
                "countryCode": "",
            },
        )
        self.logger.debug(
            "[verify_otc - %s] Request Body: %s", self.email, str(response.request.body)
        )
        self.logger.debug(
            "[verify_otc - %s] Response Status Code: %i",
            self.email,
            response.status_code,
        )
        self.logger.debug(
            "[verify_otc - %s] Response Body: %s", self.email, response.text
        )
        if response.status_code != 200:
            raise NotImplementedError(f'Unhandled Status Code "{response.status_code}"')
        self.save_session()

    def get_offers(self):
        """
        Get available offers from the web store.

        Returns:
            StoreData or None: If successful, returns StoreData; otherwise, returns None.

        Raises:
            NotImplementedError: If the request returns an unhandled status code.

        This method sends a request to retrieve available offers from the web store.
        """
        self.logger.info("Get offers for account %s", self.email)
        response = self.session.get(
            url=f"{self.BASE_URL}/store/offers?countryCode=",
            headers=self.default_headers,
        )
        self.logger.debug(
            "[get_offers - %s] Response Status Code: %i",
            self.email,
            response.status_code,
        )
        self.logger.debug(
            "[get_offers - %s] Response Body: %s", self.email, response.text
        )
        if response.status_code == 200:
            return StoreData(data=response.json())
        elif response.status_code == 401:
            return None
        raise NotImplementedError(f'Unhandled Status Code "{response.status_code}"')

    def purchase_offer(self, item_id: str, currency_type: str):
        """
        Purchase an offer from the web store.

        Args:
            item_id (str): The ID of the item to purchase.
            currency_type (str): The type of currency for the purchase.

        Returns:
            dict or None: If successful, returns the purchase response as a dictionary; otherwise, returns None.

        Raises:
            NotImplementedError: If the request returns an unhandled status code.

        This method sends a request to purchase an offer from the web store.
        """
        self.logger.info("Purchase item '%s' for account '%s'", item_id, self.email)
        response = self.session.post(
            url=f"{self.BASE_URL}/store/purchase",
            headers=self.default_headers,
            json={
                "countryCode": "DE",
                "currencyCode": "EUR",
                "currencyType": currency_type,
                "purchasePrice": 0,
                "itemId": item_id,
                "quantity": 1,
                "requestId": str(uuid4()),
            },
        )
        self.logger.debug(
            "[purchase_offer - %s] Request Body: %s",
            self.email,
            str(response.request.body),
        )
        self.logger.debug(
            "[purchase_offer - %s] Response Status Code: %i",
            self.email,
            response.status_code,
        )
        self.logger.debug(
            "[purchase_offer - %s] Response Body: %s", self.email, response.text
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            return None
        raise NotImplementedError(f'Unhandled Status Code "{response.status_code}"')

    def get_code_from_message(self, message_id):
        message = self.gmail_connector.get_message_details(message_id)
        if not message.receiver or not message.subject:
            return None
        elif self.email not in message.receiver:
            return None
        _match = self.EA_SUBJECT_PATTERN.match(message.subject)
        if not _match:
            return None
        return _match[1]

    def login(self):
        self.logger.info("Perform login for account %s", self.email)
        pre_messages_list = self.gmail_connector.get_messages()
        code = None
        self.request_otc()
        for _ in range(0, self.config.max_login_attempts):
            sleep(self.config.login_sleep_time)
            new_messages_list = self.gmail_connector.get_messages()
            has_new_messages = (
                new_messages_list.messages[0].id != pre_messages_list.messages[0].id
            )
            if not has_new_messages:
                continue
            for entry in new_messages_list.messages:
                if entry.id == pre_messages_list.messages[0].id:
                    break
                code = self.get_code_from_message(entry.id)
                if code:
                    break
            pre_messages_list = new_messages_list
            if code:
                break

        if not code:
            raise ValueError("The verification code wasn't found in the inbox!")
        self.verify_otc(code)

    def schedule_connection_check(self):
        if not self.config.is_self_scheduling:
            return
        url = "https://google.com"
        try:
            self.session.get(url, timeout=5)
            self.logger.info("Successfully pinged '%s'", url)
        except (RequestConnectionError, RequestTimeout):
            self.logger.warning(
                "No internet connection established! Unable to reach '%s'",
                url
            )
        finally:
            # TODO read delay from config
            self.scheduler.enter(1800, 1, self.schedule_connection_check)

    def schedule_ping(self):
        # TODO return if ping is disabled in config
        if not self.config.is_self_scheduling:
            return
        self.logger.info("Current queue size: %i", len(self.scheduler.queue))
        if not self.scheduler.empty():
            self.logger.info("Next run in %s", self.get_delta())
        # TODO read delay from config (min 60?)
        self.scheduler.enter(
            delay=60,
            priority=1,
            action=self.schedule_ping,
        )

    def schedule_purchase(self, delay, item_id: str, currency_type: str):
        if not self.config.is_self_scheduling and not self.config.allow_scheduling:
            return
        elif (
            self.config.allow_scheduling
            and self.config.max_delay_scheduling_time > 0
            and self.config.max_delay_scheduling_time < delay
        ):
            return
        for queue_entry in self.scheduler.queue:
            if queue_entry.action != self.purchase_offer:
                continue
            elif item_id in queue_entry.kwargs:
                self.logger.warning(
                    "Item already scheduled, skipping scheduling of item %s", item_id
                )
                return

        self.scheduler.enter(
            delay=delay,
            priority=1,
            action=self.purchase_offer,
            kwargs={"item_id": item_id, "currency_type": currency_type},
        )
        self.logger.info(
            "Successfully scheduled purchase of %s in %s",
            item_id,
            str(timedelta(seconds=delay)),
        )

    def get_delta(self):
        _now = datetime.now()
        return timedelta(seconds=self.scheduler.queue[0].time - _now.timestamp())

    def schedule_run(self, run_directly: bool):
        if not self.config.is_self_scheduling and not self.config.allow_scheduling:
            return
        elif run_directly:
            return self.run()

        purchase_queue = None
        for queue_entry in self.scheduler.queue:
            if queue_entry.action == self.purchase_offer:
                purchase_queue = queue_entry
                break

        if purchase_queue:
            self.scheduler.enterabs(purchase_queue.time + 5, 1, self.run)
            self.logger.info(
                "Successfully scheduled run after the next purchase (in %s)",
                str(self.get_delta()),
            )
            return

        self.logger.info("No purchase found to schedule run...")
        self.scheduler.enter(3600, 1, self.run)
        self.logger.info(
            "Successfully scheduled run in %s", str(timedelta(seconds=3600))
        )

    def get_free_offers(self):
        self.logger.info("Search free offers for account: %s", self.email)
        offers = self.get_offers()
        if not offers:
            self.login()
            offers = self.get_offers()
        free_offers = []
        for ws_offer in offers.web_store_offers:
            offer = ws_offer.offer
            if not offer.is_free_offer:
                continue
            self.logger.info("FreeOffer found: %s", ws_offer.item.title)
            if offer.price.purchase_amount > 0:
                self.logger.warning(
                    "Free Offer without Free price found! Please investigate..."
                )
                continue
            free_offers.append(ws_offer)
        return free_offers

    def run(self):
        self.logger.info("Getting offers...")
        offers = self.get_offers()
        purchases = 0
        if not offers:
            self.login()
            offers = self.get_offers()
        for ws_offer in offers.web_store_offers:
            offer = ws_offer.offer
            if not offer.is_free_offer:
                continue
            self.logger.info("FreeOffer found: %s", ws_offer.item.title)
            if offer.price.purchase_amount > 0:
                self.logger.warning(
                    "Free Offer without Free price found! Please investigate..."
                )
                continue
            elif offer.purchase_cooldown_left:
                self.schedule_purchase(
                    delay=offer.purchase_cooldown_left,
                    item_id=offer.id,
                    currency_type=offer.price.purchase_currency,
                )
                continue
            purchases += 1
            response = self.purchase_offer(
                item_id=offer.id, currency_type=offer.price.purchase_currency
            )
            for granted_item in response["itemsGranted"]:
                name = granted_item.get("name", "NameNotPresent")
                min_quantity = (granted_item.get("quantity") or {}).get(
                    "min", "UnkownMinCount"
                )
                max_quantity = (granted_item.get("quantity") or {}).get(
                    "max", "UnkownMinCount"
                )

                info_message = f" ItemGranted: {name} ({min_quantity}/{max_quantity})"
                self.logger.info(info_message)

        self.schedule_run(purchases > 0)

    def start(self):
        self.run()
        self.scheduler.run()
        self.logger.info("Finished script!")
