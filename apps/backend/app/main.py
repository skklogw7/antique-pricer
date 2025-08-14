import os
import time
import uuid
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client, Client
from .services.query_builder import build_query
from .services.providers.ebay_browse import EbayBrowseProvider
from .services.providers.ebay_sold_finding import EbayFindingSoldProvider

SOLD_COMPS_ENABLED = os.getenv("SOLD_COMPS_ENABLED","false").lower()=="true"
browse_provider = EbayBrowseProvider()
sold_provider = EbayFindingSoldProvider()

# --- Provider selection (Step 3a) ---
COMPS_PROVIDER = os.getenv("COMPS_PROVIDER", "ebay_browse").strip().lower()  # "ebay_browse" | "etsy"


app = FastAPI(title="Antique Pricer API")

# CORS
PROD_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://antique-pricer.vercel.app")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[PROD_ORIGIN],
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client (requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in Render env)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
sb: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/estimate")
async def estimate(
    image: UploadFile = File(...),
    category: str = Form(...),
    notes: str = Form("")
):
    """
    Saves image (Supabase if configured), builds a query from category+notes,
    fetches comps from the selected provider (ebay_browse or etsy),
    and returns a quick min/max range.

    Response includes both new fields (thumbnail/status/ended_at) and legacy
    aliases (thumb/sold_date) for compatibility with your current UI.
    """
    t0 = time.time()
    try:
        # 1) Save image (optional Supabase)
        image_url: Optional[str] = None
        content = await image.read()
        if sb:
            file_id = f"{uuid.uuid4()}-{image.filename or 'item.jpg'}"
            sb.storage.from_("uploads").upload(
                file_id, content, {"content-type": image.content_type or "image/jpeg"}
            )
            image_url = f"{SUPABASE_URL}/storage/v1/object/public/uploads/{file_id}"

        # 2) Build search query from category + notes
        #    (maps "not_sure" to a sane default via query_builder fallback)
        q = build_query(
            category if category and category != "not_sure" else None,
            notes or ""
        )

        # 3) Fetch comps from selected provider (Step 3a)
        if COMPS_PROVIDER == "etsy":
            comps_raw = await etsy_provider.search(q, limit=12)
            source_label = "etsy"
        else:
            comps_raw = await ebay_active.search(q, limit=12)
            source_label = "ebay_browse"

        # 4) Handle no-results case gracefully
        if not comps_raw:
            return {
                "normalized_title": (category or "Antique").title(),
                "value_range": {"low": 0, "high": 0, "confidence": "low"},
                "pricing_rationale": [
                    "No close matches found. Try adding maker, dimensions, condition, or clearer photo."
                ],
                "top_comps_used": [],
                "notes": [],
                "suggested_keywords": q.split()[:5],
                "comps": [],
                "image_url": image_url,
                "duration_ms": int((time.time() - t0) * 1000),
            }

        # 5) Compute a simple range (until LLM is wired on Day 4)
        priced = [c for c in comps_raw if isinstance(c.get("price"), (int, float)) and c["price"] > 0]
        if priced:
            low = min(c["price"] for c in priced)
            high = max(c["price"] for c in priced)
            confidence = "medium"
        else:
            low, high, confidence = 0, 0, "low"

        # 6) Back-compat shaping: add thumb/sold_date aliases so old UI works
        comps: List[dict] = []
        for c in comps_raw:
            thumb = c.get("thumbnail")  # new key
            ended_at = c.get("ended_at")  # new key (sold only)
            # Add legacy aliases:
            c_out = {
                **c,
                "thumb": thumb,  # legacy alias
                "sold_date": ended_at,  # legacy alias
            }
            comps.append(c_out)

        # 7) Return payload
        return {
            "normalized_title": (category or "Antique").title(),
            "value_range": {"low": low, "high": high, "confidence": confidence},
            "pricing_rationale": [
                f"Based on {len(comps)} {'sold' if comps[0].get('status')=='sold' else 'active'} comps for query: '{q}' (source: {source_label})."
            ],
            "top_comps_used": list(range(min(3, len(comps)))),
            "notes": [],
            "suggested_keywords": q.split()[:5],
            "comps": comps,
            "image_url": image_url,
            "duration_ms": int((time.time() - t0) * 1000),
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
