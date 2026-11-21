from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import get_assistant, router
from src.common.config import get_settings
from src.common.logger import setup_logger

logger = setup_logger("fastapi_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo các engine tìm kiếm và assistant khi app khởi động."""
    logger.info("Khởi động FastAPI server - Khởi tạo các engine...")
    try:
        get_assistant()
        logger.info("Khởi tạo thành công Hybrid Search và LegalRAGAssistant.")
    except Exception as e:
        logger.warning(f"Chưa thể preload assistant: {e}")
    yield
    logger.info("Đang tắt FastAPI server...")


def create_app() -> FastAPI:
    """Tạo FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="VN Legal RAG Assistant API",
        description="API Trợ lý tra cứu Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Thêm middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)
