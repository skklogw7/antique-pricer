from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Set this in Render's environment variables for production
frontend_origin = os.getenv("FRONTEND_ORIGIN", "*")  # "*" for dev, change to your Vercel domain for prod

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],  # e.g., ["https://your-frontend.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

