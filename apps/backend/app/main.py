from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Antique Pricer API")

# Exact prod origin (no trailing slash)
PROD_ORIGIN = "https://antique-pricer.vercel.app"
# Allow all Vercel preview subdomains too (optional)
PREVIEW_REGEX = r"^https://.*\.vercel\.app$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[PROD_ORIGIN],          # must be exact match
    allow_origin_regex=PREVIEW_REGEX,     # lets preview deploys call the API
    allow_credentials=True,               # fine because we’re not using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}

@app.get("/health")
def health():
    return {"ok": True}


@app.post("/estimate")
async def estimate(
    image: UploadFile = File(...),
    category: str = Form("not_sure"),
    notes: str = Form("")
):
    t0 = time.time()
    sb = supa()

    # 1) upload image
    file_id = f"{uuid.uuid4()}-{image.filename or 'item.jpg'}"
    data = await image.read()
    sb.storage.from_("uploads").upload(file_id, data, {"content-type": image.content_type})
    image_url = f'{os.environ["SUPABASE_URL"]}/storage/v1/object/public/uploads/{file_id}'

    # 2) mock tags + comps (swap with real adapters later)
    tags = {"category": category if category!="not_sure" else "furniture",
            "style": ["mid-century modern"], "materials": ["teak"]}
    comps = [
        {"title":"Mid-century teak sideboard","price":620,"sold_date":"2025-07-21","url":"https://example.com","thumb":"https://placehold.co/80"},
        {"title":"Danish teak credenza","price":540,"sold_date":"2025-07-10","url":"https://example.com","thumb":"https://placehold.co/80"}
    ]
    low, high = max(0, min(c["price"] for c in comps) - 50), max(c["price"] for c in comps)

    return {
        "normalized_title": "Mid-century teak sideboard (c. 1960s), Denmark-style",
        "value_range": {"low": low, "high": high, "confidence": "medium"},
        "pricing_rationale": ["Based on 2 recent sold comps."],
        "top_comps_used": [0,1],
        "notes": ["Avoid heavy refinishing before listing."],
        "suggested_keywords": ["mid century","teak","sideboard","Danish","credenza"],
        "comps": comps,
        "image_url": image_url,
        "duration_ms": int((time.time()-t0)*1000)
    }
