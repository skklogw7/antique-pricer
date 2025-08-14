import re
def build_query(category: str | None, notes: str | None, fallback: str = "antique furniture") -> str:
    blob = " ".join([category or "", notes or ""]).strip()
    blob = re.sub(r"\s+", " ", blob)
    return blob if len(blob) >= 3 else fallback

