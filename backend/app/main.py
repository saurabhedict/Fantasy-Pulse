import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, health, matches, pulse
from app.core.config import get_settings
from app.core.errors import AppError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.0",
                  description="Explains what is happening to a fan's fantasy cricket team, over by over.")
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list,
                       allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    for module in (health, matches, pulse, chat):
        app.include_router(module.router)
    return app


app = create_app()
