"""
Gmail Connector Module

This module provides a GmailConnector class that facilitates interaction with the Gmail API.
It allows the user to obtain credentials, access Gmail messages, and search for specific emails by subject.

Example:
    connector = GmailConnector(email='user@example.com', token_path='token.json')
    verification_code = connector.find_email_by_subject()  # Find a verification code email

"""

import os
from logging import getLogger
from typing import Optional, Union

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from core.config import Config
from core.utils import slugify
from gmail.types import GmailMessageListResponse, GmailMessageWrapper

# TODO: Update and add docstrings


class GmailConnector:
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    logger = getLogger("GmailConnector")

    def __init__(self, email: str, config: Optional[Union[str, Config]] = None):
        self.config: Config = Config.load_config(config) or Config.get_global_config()
        if config.gmail_credentials_location is None:
            raise ValueError("Gmail credentials location is not set")
        self.email: str = email
        self.token_path: str = os.path.join(
            self.config.gmail_token_location, f"{slugify(email)}_token.json"
        )
        self.creds: Optional[Credentials] = None
        self.service: Optional[Resource] = None

    def load_credentials(self):
        if self.creds:
            return
        try:
            self.creds = Credentials.from_authorized_user_file(
                self.token_path, self.SCOPES
            )
            self.logger.debug(
                "Successfully loaded credentials from file '%s'", self.token_path
            )
        except (FileNotFoundError, ValueError):
            self.logger.critical(
                "Could not load credentials from file '%s'", self.token_path
            )

    def get_new_credentials(self):
        """
        Obtains new credentials and saves them in the specified file.

        This method initiates the authorization flow and saves the generated credentials to
        the file specified in the constructor (token_path).
        """
        flow = InstalledAppFlow.from_client_secrets_file(
            self.config.gmail_credentials_location, self.SCOPES
        )
        self.creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(self.token_path, "w", encoding="utf-8") as f:
            f.write(self.creds.to_json())

    def ensure_credentials(self, force_renew: bool = False):
        """
        Ensure the presence of valid credentials or renew them if necessary.
        This method checks if valid credentials exist for the Gmail API.
        If they don't or if 'force_renew' is set to True, it initiates the
        authorization flow to obtain new credentials and saves them in the
        specified file (token_path).

        Args:
            force_renew (bool, optional): If True, credentials will be renewed
            regardless of their current validity.

        Returns:
            bool: True if credentials were renewed or needed to be renewed,
            False if existing credentials are valid.

        Note:
            If the credentials need to be renewed, this method will attempt
            to refresh them. If an HTTP error occurs during the refresh process,
            it will fall back to obtaining new credentials.
        """
        self.load_credentials()
        if force_renew or not self.creds:
            self.get_new_credentials()
            return True
        elif self.creds.valid:
            return False
        try:
            self.creds.refresh(Request())
        except (HttpError, RefreshError):
            self.get_new_credentials()
        return True

    def ensure_service(self):
        """
        Ensures that the Gmail API service is available and authenticated.

        If valid credentials are already available, it will reuse them to build the service.
        If credentials need to be renewed or if the service is not yet created, it will initialize
        a new service using the credentials.

        This function should be called before using any methods that require the Gmail API service.

        """
        refreshed = self.ensure_credentials()
        if self.service and not refreshed:
            return
        self.service = build("gmail", "v1", credentials=self.creds, cache_discovery=False)

    def get_messages(self):
        """
        Retrieves a list of email messages from the user's Gmail inbox.

        Returns:
            list: A list of email message metadata.
        """
        self.ensure_service()
        try:
            # pylint: disable=no-member
            return GmailMessageListResponse(
                self.service.users().messages().list(userId="me").execute()
            )
        except HttpError:
            # TODO add proper error handling
            return []

    def get_message_details(self, message_id):
        """
        Retrieves the details of a specific email message.

        Args:
            message_id (str): The ID of the email message.

        Returns:
            dict: Details of the email message.
        """
        self.ensure_service()
        try:
            # pylint: disable=no-member
            return GmailMessageWrapper(
                self.service.users()
                .messages()
                .get(userId="me", id=message_id)
                .execute()
            )
        except HttpError:
            # TODO add proper error handling
            return None
