import os
import time
import uuid
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client, Client

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
    t0 = time.time()
    try:
        # 1) Save image to Supabase Storage if configured; otherwise skip
        image_url = None
        content = await image.read()
        if sb:
            file_id = f"{uuid.uuid4()}-{image.filename or 'item.jpg'}"
            sb.storage.from_("uploads").upload(
                file_id, content, {"content-type": image.content_type or "image/jpeg"}
            )
            image_url = f"{SUPABASE_URL}/storage/v1/object/public/uploads/{file_id}"

        # 2) Mock tags + comps (swap with real on later days)
        tags = {
            "category": category if category != "not_sure" else "furniture",
            "style": ["mid-century modern"],
            "materials": ["teak"],
        }
        comps = [
            {"title": "Mid-century teak sideboard", "price": 620, "sold_date": "2025-07-21", "url": "https://example.com/a", "thumb": "https://placehold.co/80"},
            {"title": "Danish teak credenza", "price": 540, "sold_date": "2025-07-10", "url": "https://example.com/b", "thumb": "https://placehold.co/80"},
        ]
        low = max(0, min(c["price"] for c in comps) - 50)
        high = max(c["price"] for c in comps)

        return {
            "normalized_title": f"{category.title()} item (mock)",
            "value_range": {"low": low, "high": high, "confidence": "medium"},
            "pricing_rationale": ["Mock estimate based on 2 placeholder comps."],
            "top_comps_used": [0, 1],
            "notes": ["Replace with real comps and LLM."],
            "suggested_keywords": ["mid century", "teak", "sideboard"],
            "comps": comps,
            "image_url": image_url,
            "duration_ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

