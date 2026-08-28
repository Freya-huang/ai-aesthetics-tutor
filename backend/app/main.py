import logging
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.common.exceptions import register_exception_handlers
from app.knowledge_base.router import router as knowledge_router
from app.art_diagnosis.router import router as art_diagnosis_router
from app.paper_interpreter.router import router as paper_interpreter_router
from app.chat_tutor.router import router as chat_tutor_router

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="AI美学导师后端API - 提供作品诊断、论文解读和知识库检索服务",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(knowledge_router)
app.include_router(art_diagnosis_router)
app.include_router(paper_interpreter_router)
app.include_router(chat_tutor_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "mock_mode": settings.mock_mode,
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name} API",
        "docs": "/docs",
        "health": "/health",
        "mock_mode": settings.mock_mode,
    }


@app.on_event("startup")
async def startup_event():
    settings.ensure_directories()
    logger.info(f"Starting {settings.app_name} v1.0.0")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Mock mode: {settings.mock_mode}")
    logger.info(f"Temp directory: {settings.temp_dir}")
    logger.info(f"Knowledge base directory: {settings.knowledge_base_dir}")
    logger.info("All routes registered successfully")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
