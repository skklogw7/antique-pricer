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

