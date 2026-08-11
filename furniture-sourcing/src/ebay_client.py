import base64
import time
from typing import List, Optional

import requests


class EbayClient:
    """Thin wrapper around eBay's official Browse API (client-credentials flow).

    Requires a free eBay Developer account: https://developer.ebay.com
    Create a "Production" keyset for an app and use its Client ID / Client Secret.
    """

    TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    SCOPE = "https://api.ebay.com/oauth/api_scope"

    def __init__(self, client_id: str, client_secret: str, marketplace_id: str = "EBAY_GB"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.marketplace_id = marketplace_id
        self._token = None
        self._token_expiry = 0

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token

        credentials = f"{self.client_id}:{self.client_secret}"
        b64 = base64.b64encode(credentials.encode()).decode()
        resp = requests.post(
            self.TOKEN_URL,
            headers={
                "Authorization": f"Basic {b64}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials", "scope": self.SCOPE},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 7200)
        return self._token

    def search(
        self,
        query: str,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        category_ids: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id,
        }

        filters = ["deliveryCountry:GB"]
        if price_min is not None or price_max is not None:
            lo = "" if price_min is None else price_min
            hi = "" if price_max is None else price_max
            filters.append(f"price:[{lo}..{hi}],priceCurrency:GBP")

        params = {"q": query, "limit": limit, "filter": ",".join(filters)}
        if category_ids:
            params["category_ids"] = category_ids

        resp = requests.get(self.SEARCH_URL, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json().get("itemSummaries", [])
