from dataclasses import dataclass
from typing import Optional


@dataclass
class Listing:
    source: str  # "ebay" or "facebook"
    external_id: str
    title: str
    price: Optional[float]
    currency: str
    url: str
    location: Optional[str]
    image_url: Optional[str]
    search_term: str
