import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routes import auth, butler, dashboard, planning, profile, tools, transactions
from app.utils.errors import register_error_handlers

logger = logging.getLogger("ai_butler")

PRIVACY_STATEMENT = ("Your financial information is entered manually by you. "
                     "This application does not connect to your bank account.")

app = FastAPI(title="AI Butler API", version="1.0.0",
              description="Manual-entry personal finance assistant. It analyses, calculates, explains "
                          "and warns. It never moves money.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


@app.exception_handler(Exception)
async def unexpected_error(_: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        {"error": {"code": "server_error", "message": "Something went wrong on our side. Please try again.",
                   "details": None}},
        status_code=500,
    )


for module in (auth, profile, transactions, dashboard, tools, butler):
    app.include_router(module.router)
for router in planning.routers:
    app.include_router(router)


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get("/api/privacy", tags=["meta"])
def privacy():
    return {"statement": PRIVACY_STATEMENT}