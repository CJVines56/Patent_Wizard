from fastapi import FastAPI
from app.api.routes import router as api_router

app = FastAPI(title="Your Project API")
app.include_router(api_router, prefix="/api")

@app.get("/api/health")
def health():
    return {"ok": True}