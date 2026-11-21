import logging
import sys
from pathlib import Path
from src.common.config import get_settings


def setup_logger(name: str = "vn_legal_rag", level: int = logging.INFO) -> logging.Logger:
    """Khởi tạo và cấu hình logger chuẩn cho dự án."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Tránh gắn nhiều handler trùng lặp
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Stream Handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler (logs/app.log)
        try:
            settings = get_settings()
            logs_dir = settings.LOGS_DIR
            logs_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(logs_dir / "app.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass

    return logger


def get_logger(name: str) -> logging.Logger:
    """Lấy logger con theo tên module."""
    return logging.getLogger(f"vn_legal_rag.{name}")
