from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
import uuid
from fastapi import HTTPException
from pydantic import BaseModel
import jwt
from fastapi.responses import JSONResponse
import os
import yaml
from dotenv import load_dotenv
from fastapi import Header
from typing import List


API_KEY = "ak_sqtgfvbrjoywro0oboayg8x8"

class Event(BaseModel):
    user: str
    amount: float
    ts: int

class AnalyticsRequest(BaseModel):
    events: List[Event]


app = FastAPI()
load_dotenv()
DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# Replace with your logged-in email exactly
EMAIL = "24f2006966@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://dash-h91voj.example.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        response.headers["X-Request-ID"] = str(uuid.uuid4())
        response.headers["X-Process-Time"] = f"{duration:.6f}"

        return response


app.add_middleware(HeaderMiddleware)


@app.get("/stats")
async def stats(values: str = Query(...)):
    nums = [int(x.strip()) for x in values.split(",") if x.strip()]

    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums),
    }
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

class TokenRequest(BaseModel):
    token: str
@app.post("/verify")
async def verify(req: TokenRequest):
    try:
        payload = jwt.decode(
            req.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer="https://idp.exam.local",
            audience="tds-k31vdkvs.apps.exam.local",
        )

        return {
            "valid": True,
            "email": payload["email"],
            "sub": payload["sub"],
            "aud": payload["aud"],
        }


# ...

    except Exception:
        return JSONResponse(
            status_code=401,
            content={"valid": False}
        )

@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    # YAML layer
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml", "r") as f:
            data = yaml.safe_load(f)
            if data:
                config.update(data)

    # .env layer
    if os.getenv("NUM_WORKERS"):
        config["workers"] = os.getenv("NUM_WORKERS")

    if os.getenv("APP_API_KEY"):
        config["api_key"] = os.getenv("APP_API_KEY")

    # OS environment layer
    if os.getenv("APP_LOG_LEVEL"):
        config["log_level"] = os.getenv("APP_LOG_LEVEL")

    if os.getenv("APP_API_KEY"):
        config["api_key"] = os.getenv("APP_API_KEY")

    # CLI overrides (?set=key=value)
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key in ("port", "workers"):
            value = int(value)
        elif key == "debug":
            value = value.lower() in ("true", "1", "yes", "on")

        config[key] = value

    # Type coercion
    config["port"] = int(config["port"])
    config["workers"] = int(config["workers"])

    if not isinstance(config["debug"], bool):
        config["debug"] = str(config["debug"]).lower() in (
            "true",
            "1",
            "yes",
            "on",
        )

    # Always mask the API key
    config["api_key"] = "****"

    return config

@app.post("/analytics")
async def analytics(
    req: AnalyticsRequest,
    x_api_key: str | None = Header(default=None)
):
    if x_api_key != API_KEY:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized"}
        )

    total_events = len(req.events)
    unique_users = len({e.user for e in req.events})

    revenue = 0.0
    user_totals = {}

    for event in req.events:
        if event.amount > 0:
            revenue += event.amount
            user_totals[event.user] = (
                user_totals.get(event.user, 0) + event.amount
            )

    top_user = max(user_totals, key=user_totals.get) if user_totals else ""

    return {
        "email": "24f2006966@ds.study.iitm.ac.in",
        "total_events": total_events,
        "unique_users": unique_users,
        "revenue": revenue,
        "top_user": top_user,
    }
    