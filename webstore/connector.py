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
from typing import Optional, Union, Type
from uuid import uuid4
from urllib import parse as urlparse

from requests import ConnectionError as RequestConnectionError
from requests import Session
from requests import Timeout as RequestTimeout

from core.config import Config
from core.utils import slugify
from gmail.connector import GmailConnector

# TODO: Move scheduler logic to own class
# TODO: Update and add docstrings

class EAWebstoreConnector:
    """
    A class for connecting to and interacting with the
    Lord of the Rings - Heroes of Middleearth web store.

    Args:
        email (str): The email associated with the user's account.

    This class provides methods for requesting one-time codes (OTC),
    verifying codes, retrieving offers, and purchasing items from the web store.
    """

    BASE_URL = None
    EA_ACCOUNTS_AUTH_URL = "https://accounts.ea.com/connect/auth?mode=junoNff&client_id=SWGOH_SERVER_WEB_APP&response_type=code&hide_create=true&redirect_uri=https://store.galaxy-of-heroes.starwars.ea.com"
    
    EA_SUBJECT_PATTERN = re.compile("^Verification Code For EA[^0-9]*([0-9]+)$")
    SESSION_FILENAME_PREFIX = ''
    session_class: Type['Session'] = Session
    logger = logging.getLogger("EAWebstoreConnector")

    def __init__(self, email: str, config: Optional[Union[str, Config]] = None):
        self.config: Config = Config.load_config(config) or Config.get_global_config()
        self.email: str = email
        try:
            self.gmail_connector: GmailConnector = GmailConnector(
                email=email, config=self.config
            )
        except ValueError as e:
            self.logger.error(e)
            self.gmail_connector = None
        self.session_filename: str = os.path.join(
            self.config.webstore_sessions_location,
            f"{self.SESSION_FILENAME_PREFIX}{slugify(email)}_session.pickle",
        )
        self.session = self.session_class()
        self.scheduler = scheduler(time, sleep)
        self.logger.setLevel(self.config.webstore_log_level)
        self.auth_id = None

        # Attempt to load the session from a file
        if os.path.exists(self.session_filename):
            self.load_session()

        self.schedule_ping()
        self.schedule_connection_check()

    def get_default_headers(self):
        if self.auth_id:
            return {
                'X-Rpc-Auth-Id': self.auth_id,
                "Accept-Language": "DE"
            }
        return {
            "Accept-Language": "DE"
        }

    def load_session(self):
        """
        Load and deserialize a session object from a file.
        """
        with open(self.session_filename, "rb") as file:
            self.session = pickle.load(file)
        self.logger.debug(
            "Successfully loaded session from file '%s'", self.session_filename
        )

    def save_session(self):
        """
        Serialize and save the session object to a file.
        """
        with open(self.session_filename, "wb") as file:
            pickle.dump(self.session, file)
        self.logger.debug(
            "Successfully saved session to file '%s'", self.session_filename
        )

    def _wrap_offers(self, data):
        raise NotImplementedError

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
            headers=self.get_default_headers(),
        )
        self.logger.debug(
            "[get_offers - %s] Response Status Code: %i",
            self.email,
            response.status_code,
        )
        if response.status_code == 200:
            return self._wrap_offers(response.json())
        elif response.status_code == 401:
            return None
        raise NotImplementedError(f'Unhandled Status Code "{response.status_code}": {response.text}')

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
            headers=self.get_default_headers(),
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
        if not self.gmail_connector:
            return None
        message = self.gmail_connector.get_message_details(message_id)
        if not message.receiver or not message.subject:
            return None
        elif self.email not in message.receiver:
            return None
        _match = self.EA_SUBJECT_PATTERN.match(message.subject)
        if not _match:
            return None
        return _match[1]

    def login(self, force_login: bool = False) -> None:
        """
        Logs into the webstore.

        Args:
            force_login (bool, optional): If True, forces the login even if already logged in. Defaults to False.

        Raises:
            Exception: If failed to get the accounts URL.

        Returns:
            None
        """
        if not force_login and self.auth_id:
            return
        self.logger.info("Perform login for account %s", self.email)
        self.logger.debug("Send auth0 request...")
        response = self.session.get(self.EA_ACCOUNTS_AUTH_URL)
        if response.status_code != 200:
            raise Exception("Failed to get accounts URL")
        
        # Check if it's already the code, we can skip the login process
        _parsed = urlparse.urlparse(response.url)
        save = False
        if "code" in urlparse.parse_qs(_parsed.query):
            self.logger.debug("Code found in URL, skipping login process...")
            code = urlparse.parse_qs(_parsed.query)["code"][0]
        else:
            self.logger.debug("Perform login process...")
            code = self._perform_login(response.url)
            save = True
        
        self._finish_login(code)
        if save:
            self.save_session()

    def _perform_login(self, url: str) -> str:
        """
        Performs the login process for the webstore.

        Args:
            url (str): The URL of the signin page.

        Returns:
            str: The code obtained from the redirect location.

        Raises:
            Exception: If any step of the login process fails.
        """
        response = self.session.get(url)
        if response.status_code != 200:
            # TODO: improve error handling
            raise Exception("Failed to get signin page")
        self.logger.debug("Submit email...")
        pre_message_list = self._get_messages()
        response = self.session.post(url, data={
            "email": self.email,
            "_eventId": "submit",
            "thirdPartyCaptchaResponse": "",
            "_rememberMe": "on",
            "rememberMe": "on"
        })
        if response.status_code != 200:
            # TODO: improve error handling
            raise Exception("Failed to submit email")
        code = self._get_code_from_gmail_account(pre_message_list)
        if not code:
            print("Failed to get code from Gmail account.")
            code = input("Enter the code: ")
        response = self.session.post(response.url, data={
            "oneTimeCode": code,
            "_eventId": "submit",
        })
        if response.status_code != 200:
            # TODO: improve error handling
            raise Exception("Failed to submit code")

        _parsed = urlparse.urlparse(response.url)
        if "code" not in urlparse.parse_qs(_parsed.query):
            # TODO: improve error handling
            raise Exception("Failed to get code in redirect location")
        
        return urlparse.parse_qs(_parsed.query)["code"][0]

    def _finish_login(self, code):
        """
        Completes the login process by sending the access code to the server and retrieving the authentication ID.

        Args:
            code (str): The access code obtained during the login process.

        Returns:
            None

        Raises:
            KeyError: If the authentication ID cannot be retrieved from the server response.

        """
        finish = self.session.post("https://store.galaxy-of-heroes.starwars.ea.com/auth/access_code", json={
            "access_code": code,
            "redirect_uri": "https://store.galaxy-of-heroes.starwars.ea.com"
        })
        self.auth_id = finish.json()["authId"]

    def _get_messages(self):
        if not self.gmail_connector:
            return None
        self.logger.debug("Get messages...")
        return self.gmail_connector.get_messages()

    def _get_code_from_gmail_account(self, pre_messages_list: Optional[list]):
        if not self.gmail_connector or pre_messages_list is None:
            return None
        code = None
        self.logger.debug("Get messages...")
        for _ in range(0, self.config.max_login_attempts):
            sleep(self.config.login_sleep_time)
            new_messages_list = self._get_messages()
            if not new_messages_list:
                self.logger.debug("No messages found, retrying...")
                continue
            # TODO: In case the prev. Code wasn't used the same code is send which results in the check evaluating to False. This should be fixed.
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
        return code

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
            self.logger.info(
                "Scheduling is deactivated! Item \"%s\" will be available in %s",
                item_id,
                str(timedelta(seconds=delay)),
            )
            return
        elif (
            self.config.allow_scheduling
            and self.config.max_delay_scheduling_time > 0
            and self.config.max_delay_scheduling_time < delay
        ):
            self.logger.info(
                "The delay exceeds the max allowed delay! Item \"%s\" will be available in %s",
                item_id,
                str(timedelta(seconds=delay)),
            )
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

    def schedule_run(self, run_directly: bool = False):
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
        elif self.config.allow_scheduling:
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

    def _handle_offers(self, offers) -> bool:
        raise NotImplementedError

    def run(self):
        self.login()
        self.logger.info("Getting offers...")
        offers = self.get_offers()
        run_directly = self._handle_offers(offers)
        self.schedule_run(run_directly)

    def start(self):
        self.run()
        self.scheduler.run()
        self.logger.info("Finished script!")
