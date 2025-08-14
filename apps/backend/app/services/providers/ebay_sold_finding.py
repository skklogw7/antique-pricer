import os, urllib.parse, httpx, datetime as dt
from typing import List, Optional
from ..comps import CompsProvider, Comp
EBAY_APP_ID=os.getenv("EBAY_APP_ID","")
URL="https://svcs.ebay.com/services/search/FindingService/v1"
class EbayFindingSoldProvider(CompsProvider):
    async def search(self, query:str, category_id:Optional[str]=None, limit:int=12)->List[Comp]:
        if not EBAY_APP_ID: return []
        p={"OPERATION-NAME":"findCompletedItems","SERVICE-VERSION":"1.13.0",
           "SECURITY-APPNAME":EBAY_APP_ID,"RESPONSE-DATA-FORMAT":"JSON","REST-PAYLOAD":"true",
           "keywords":query,"itemFilter(0).name":"SoldItemsOnly","itemFilter(0).value":"true",
           "paginationInput.entriesPerPage":str(limit),"sortOrder":"EndTimeSoonest"}
        if category_id: p["categoryId"]=category_id
        async with httpx.AsyncClient(timeout=8) as c:
            r=await c.get(URL+"?"+urllib.parse.urlencode(p))
            if r.status_code!=200: return []
            j=r.json()
        items=(j.get("findCompletedItemsResponse",[{}])[0].get("searchResult",[{}])[0].get("item",[]))
        out:List[Comp]=[]
        for it in items:
            try:
                price=float(it.get("sellingStatus",[{}])[0].get("currentPrice",[{}])[0].get("__value__",0) or 0)
                out.append({"title":it.get("title",[""])[0],"price":round(price,2),"currency":"USD",
                            "url":it.get("viewItemURL",[""])[0] or "","thumbnail":it.get("galleryURL",[""])[0] or None,
                            "source":"ebay_sold","status":"sold","ended_at":it.get("listingInfo",[{}])[0].get("endTime",[""])[0][:10] or str(dt.date.today())})
            except Exception: continue
        return out[:limit]

