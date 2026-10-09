from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.admin_api import router as admin_router
from app.ask_api import router as ask_router
from app.auth_api import router as auth_router
from app.knowledge_api import router as knowledge_router
from app.official_api import admin_router as official_admin_router
from app.official_api import public_router as official_public_router
from app.subscription_api import router as subscription_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="WaterQualityDecoding API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)
app.include_router(ask_router)
app.include_router(admin_router)
app.include_router(knowledge_router)
app.include_router(official_public_router)
app.include_router(official_admin_router)
app.include_router(subscription_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "wqd-backend"}
