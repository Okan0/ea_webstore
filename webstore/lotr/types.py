"""
Data wrappers for the EA Heroes of Middle Earth Webstore Offer API response.

This module contains classes that serve as data wrappers for variouselements of the webstore offer API response.
These classes help structure and access the information provided by the API in a more organized manner.
"""
from typing import List, Dict, Union


class OfferPrice:
    """
    Represents an offer price.

    Attributes:
        purchase_currency (str): The currency for the purchase price.
            In Testdata only:
                - (Empty String)
                - PREMIUM
        purchase_amount (float): The price?
    Note:
        Some additional attributes / entries are available,
        but currently not required.
    """

    def __init__(self, data: dict):
        self.purchase_currency: str = data["purchaseCurrency"]
        self.purchase_amount: float = data["purchaseAmount"]


class CurrencyItem:
    """
    Represents a currency item.

    Attributes:
        currency_id (str): The currency ID.
            Available Ids:
                livecampaign_supplies
                raid_supply
                shard_coin
                GUILD
                ENERGY_REFILL
                UNIT_XP
                livecampaign_points
                PREMIUM
                challenge
                GRIND
                ARENA
        quantity (int): The quantity of the currency item.
    """

    def __init__(self, data: dict):
        self.currency_id: str = data["currencyId"]
        self.quantity: int = data["quantity"]


class OfferRating:
    """
    Represents the price for an real money offer.

    Attributes:
        currency (str): The currency for the offer rating.
        original_total_price (float): The original total price.
        final_total_amount (float): The final total amount.
        total_discount_amount (float): The total discount amount.
        total_discount_rate (float): The total discount rate.
        promotion (List[Union[str, Dict[str, Union[str, int]]]): The list of promotions.
    """

    def __init__(self, data: dict):
        self.currency: str = data["currency"]
        self.original_total_price: float = data["originalTotalPrice"]
        self.final_total_amount: float = data["finalTotalAmount"]
        self.total_discount_amount: float = data["totalDiscountAmount"]
        self.total_discount_rate: float = data["totalDiscountRate"]
        self.promotion: List[Union[str, Dict[str, Union[str, int]]]] = data["promotion"]


class Offer:
    """
    Represents an offer.

    Attributes:
        id (str): The offer ID.
        purchase_count (int): The purchase count.
        purchase_limit (int): The purchase limit.
        price (OfferPrice): The offer price.
        promo_price (OfferPrice): The promotional offer price.
        promo_expire_time (int): The promotional offer expiration time.
        offer_purchase_limit (int): The offer purchase limit.
        sale_duration (str): The sale duration.
        start_time (int): The start time of the offer.
        end_time (int): The end time of the offer.
        offer_rating (OfferRating): Priceinformation for real money offers.
        offer_duration_left (int): The time left for the offer.
        real_money_offer (bool): Indicates if it's a real money offer.
        is_free_offer (bool): Indicates if it's a free offer.
        purchase_cooldown_left (int): seconds left until the offer is available

    Note:
        Some additional attributes / entries are available,
        but currently not required.
    """

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.purchase_count: int = data["purchaseCount"]
        self.purchase_limit: int = data["purchaseLimit"]
        self.price: OfferPrice = OfferPrice(data["price"])
        # Difference between "price" and "promoPrice"?
        # TODO: Check
        self.promo_price: OfferPrice = OfferPrice(data["promoPrice"])
        self.promo_expire_time: int = data["promoExpireTime"]
        self.offer_purchase_limit: int = data["offerPurchaseLimit"]
        self.sale_duration: str = data["saleDuration"]
        # this is currently not used in the lotr webstore, but in the swgoh webstore
        self.start_time: int = data["startTime"]
        # this is currently not used in the lotr webstore, but in the swgoh webstore
        self.end_time: int = data["endTime"]
        self.offer_rating: OfferRating = data["offerRating"]
        self.offer_duration_left: int = data["offerDurationLeft"]
        self.real_money_offer: bool = data["realMoneyOffer"]
        self.is_free_offer: bool = data["isFreeOffer"]
        self.purchase_cooldown_left: int = data["purchaseCooldownDurationLeft"]


class Item:
    """
    Represents an offer item.

    Attributes:
        title (str): The display name of the offer.

    Note:
        Some additional attributes / entries are available,
        but currently not required.
    """

    def __init__(self, data: dict):
        self.title: str = data["title"]


class WebStoreOffer:
    """
    Represents a web store offer.

    Attributes:
        offer (Offer): The offer associated with the web store offer.
        item (Item): The item associated with the web store offer.
    """

    def __init__(self, data: dict):
        self.offer: Offer = Offer(data["offer"])
        self.item: Item = Item(data["item"])


class StoreData:
    """
    Represents store data.

    Attributes:
        web_store_offers (List[WebStoreOffer]): List of web store offers.
        store_layout_id (str): The store layout ID.
        mapped_currency_code (str): The mapped currency code. (EUR)
        mapped_country_code (str): The mapped country code. (DE)
        currency_items (List[CurrencyItem]): List of currency items.
    """

    def __init__(self, data: dict):
        self.web_store_offers: List[WebStoreOffer] = [
            WebStoreOffer(offer_data) for offer_data in data.get("webStoreOffers", [])
        ]
        self.store_layout_id: str = data.get("storeLayoutId")
        # DE
        self.mapped_currency_code: str = data.get("mappedCurrencyCode")
        # EUR
        self.mapped_country_code: str = data.get("mappedCountryCode")
        # Available Ressources in the account??
        self.currency_items: List[CurrencyItem] = [
            CurrencyItem(currency_data)
            for currency_data in data.get("currencyItems", [])
        ]
