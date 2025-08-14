import os, time, re, httpx
from typing import List, Optional
from ..comps import CompsProvider, Comp

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID","")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET","")
EBAY_ENV = os.getenv("EBAY_ENV","PRODUCTION").upper()

OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token" if EBAY_ENV=="PRODUCTION" else "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
BROWSE_URL= "https://api.ebay.com/buy/browse/v1/item_summary/search" if EBAY_ENV=="PRODUCTION" else "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"

_token = {"val": None, "exp": 0}

def _need_token() -> bool: return (not _token["val"]) or time.time() > _token["exp"]-60
def _kw(q:str)->str: return " ".join(re.findall(r"[a-zA-Z0-9]+", q)[:12]) or "antique furniture"

def _rank(comps: List[Comp], q:str)->List[Comp]:
    qs=set(w.lower() for w in re.findall(r"[a-z0-9]+", q))
    def score(c:Comp)->int:
        ts=set(w.lower() for w in re.findall(r"[a-z0-9]+", c.get("title","")))
        return len(qs & ts)
    return sorted(comps, key=score, reverse=True)

async def _get_token()->str:
    if not EBAY_CLIENT_ID or not EBAY_CLIENT_SECRET: return ""
    if not _need_token(): return _token["val"] or ""
    data = {"grant_type":"client_credentials",
            "scope":"https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.browse.readonly"}
    async with httpx.AsyncClient(timeout=8) as c:
        r=await c.post(OAUTH_URL,data=data,auth=(EBAY_CLIENT_ID,EBAY_CLIENT_SECRET))
        r.raise_for_status(); j=r.json()
    _token["val"]=j["access_token"]; _token["exp"]=time.time()+int(j.get("expires_in",7200))
    return _token["val"]

class EbayBrowseProvider(CompsProvider):
    async def search(self, query:str, category_id:Optional[str]=None, limit:int=12)->List[Comp]:
        tok=await _get_token()
        if not tok:
            return [
                {"title":"Vintage teak credenza","price":599,"currency":"USD","url":"https://www.ebay.com","thumbnail":None,"source":"ebay_browse","status":"active"},
                {"title":"Mid-century sideboard","price":675,"currency":"USD","url":"https://www.ebay.com","thumbnail":None,"source":"ebay_browse","status":"active"},
                {"title":"Danish teak buffet","price":725,"currency":"USD","url":"https://www.ebay.com","thumbnail":None,"source":"ebay_browse","status":"active"},
            ]
        params={"q":_kw(query),"limit":str(limit)}
        if category_id: params["category_ids"]=category_id
        headers={"Authorization":f"Bearer {tok}"}
        async with httpx.AsyncClient(timeout=8) as c:
            r=await c.get(BROWSE_URL,headers=headers,params=params); r.raise_for_status(); data=r.json()
        items=data.get("itemSummaries",[]) or []
        out:List[Comp]=[]
        for it in items:
            price=it.get("price",{}); img=it.get("thumbnailImages") or it.get("image",{})
            thumb = (isinstance(img,list) and img and img[0].get("imageUrl")) or (isinstance(img,dict) and img.get("imageUrl")) or None
            out.append({"title":it.get("title",""),
                        "price":float(price.get("value",0) or 0),
                        "currency":price.get("currency","USD"),
                        "url":it.get("itemWebUrl") or it.get("itemHref") or "",
                        "thumbnail":thumb,"source":"ebay_browse","status":"active","ended_at":None})
        out=[c for c in out if c.get("price",0)>0]
        return _rank(out, query)[:limit]

