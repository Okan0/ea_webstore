from typing import List, Optional

class StoreItem:
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.name: str = data.get("name", "")
        self.description: str = data.get("description", "")
        self.image: str = data.get("image", "")
        self.order: int = data.get("order", 0)
        self.storeTab: str = data.get("storeTab", "")
        self.offers: List[Offer] = [Offer(offer_data) for offer_data in data.get("offers", [])]
        self.bucketItems: List[BucketItem] = [BucketItem(item_data) for item_data in data.get("bucketItems", [])]
        self.startTime: int = data.get("startTime", 0)
        self.endTime: int = data.get("endTime", 0)
        self.promoText1: str = data.get("promoText1", "")
        self.guarantee: str = data.get("guarantee", "")
        self.detailedDescription: str = data.get("detailedDescription", "")
        self.quantityImage: Optional[str] = data.get("quantityImage")
        self.quantity: Optional[str] = data.get("quantity")
        self.bonusQuantity: Optional[str] = data.get("bonusQuantity")
        self.showDetails: bool = data.get("showDetails", False)
        self.specialValue: str = data.get("specialValue", "")
        self.packOddsIdentifier: str = data.get("packOddsIdentifier", "")
        self.priceDiscountStyle: str = data.get("priceDiscountStyle", "")
        self.promoTimerDisplay: str = data.get("promoTimerDisplay", "")
        self.hideTimerThresholdDays: int = data.get("hideTimerThresholdDays", 0)
        self.showPackOdds: bool = data.get("showPackOdds", False)

class Offer:
    def __init__(self, data: dict):
        self.inAppProductId: str = data.get("inAppProductId", "")
        self.currencyType: str = data.get("currencyType", "")
        self.price: int = data.get("price", 0)
        self.availableAtEpoch: int = data.get("availableAtEpoch", 0)
        self.localPrice: float = data.get("localPrice", 0.0)
        self.countryCode: str = data.get("countryCode", "")
        self.currencyCode: str = data.get("currencyCode", "")
        self.finalTotalAmount: float = data.get("finalTotalAmount", 0.0)
        self.totalDiscountAmount: float = data.get("totalDiscountAmount", 0.0)
        self.totalDiscountRate: float = data.get("totalDiscountRate", 0.0)
        self.promotions: List[Promotion] = [Promotion(promotion_data) for promotion_data in data.get("promotions", [])]

class BucketItem:
    def __init__(self, data: dict):
        self.id: str = data.get("id", "")
        self.quantity: Optional[str] = data.get("quantity")

class Promotion:
    def __init__(self, data: dict):
        self.discountAmount: float = data.get("discountAmount", 0.0)
        self.discountRate: float = data.get("discountRate", 0.0)
        self.usage: int = data.get("usage", 0)
        self.startDate: str = data.get("startDate", "")
        self.endDate: str = data.get("endDate", "")

class StoreData:
    def __init__(self, data: dict):
        self.items: List[StoreItem] = [StoreItem(item) for item in data.get('items', [])]
