import logging
from datetime import datetime, timezone
from webstore.connector import EAWebstoreConnector
from webstore.swgoh.store_types import StoreData

class SwgohWebstoreConnector(EAWebstoreConnector):
    """
    A class for connecting to and interacting with the
    Lord of the Rings - Heroes of Middleearth web store.

    Args:
        email (str): The email associated with the user's account.

    This class provides methods for requesting one-time codes (OTC),
    verifying codes, retrieving offers, and purchasing items from the web store.
    """

    BASE_URL = 'https://store.galaxy-of-heroes.starwars.ea.com'
    SESSION_FILENAME_PREFIX = 'swgoh_'
    logger = logging.getLogger("SwgohWebstoreConnector")

    def _wrap_offers(self, data):
        return StoreData(data=data)

    def _handle_offers(self, offers: StoreData):
        now = datetime.now(tz=timezone.utc)
        purchases = 0
        for item in offers.items:
            free_offers = [o for o in item.offers if o.currencyType == 'FREE']
            if not free_offers:
                continue
            free_offer = free_offers.pop(0)
            start_time = datetime.fromtimestamp(item.startTime, tz=timezone.utc)
            end_time = datetime.fromtimestamp(item.endTime, tz=timezone.utc)
            available_at = None
            if free_offer.availableAtEpoch is not None:
                available_at = datetime.fromtimestamp(free_offer.availableAtEpoch, tz=timezone.utc)
            if now < start_time:
                self.logger.info("%s will be available at %s", item.name, str(start_time))
                continue
            if end_time < now:
                self.logger.info("%s alread expired at %s", item.name, str(end_time))
                continue
            if not available_at or now < available_at:
                delay = datetime.fromtimestamp(free_offer.availableAtEpoch, tz=timezone.utc) - now
                self.schedule_purchase(
                    delay=delay.seconds,
                    item_id=item.id,
                    currency_type=free_offer.currencyType
                )
                continue
            self.logger.info("FreeOffer found: %s", item.name)
            self.purchase_offer(item.id, free_offer.currencyType)
            purchases += 1
        return purchases > 0
