from typing import TypedDict, List, Optional

class Comp(TypedDict, total=False):
    title: str
    price: float
    currency: str
    url: str
    thumbnail: Optional[str]
    source: str            # "ebay_browse" | "ebay_sold"
    status: str            # "active" | "sold"
    ended_at: Optional[str]# YYYY-MM-DD if sold

class CompsProvider:
    async def search(self, query: str, category_id: Optional[str] = None, limit: int = 12) -> List[Comp]:
        raise NotImplementedError

