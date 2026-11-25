from typing import List, Optional
from openai import OpenAI

from src.common.config import get_settings
from src.common.logger import get_logger

logger = get_logger("llm_client")


class OpenRouterLLMClient:
    """Client giao tiếp với LLM API (hỗ trợ Groq tốc độ cao và OpenRouter dự phòng)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self.provider = getattr(settings, "LLM_PROVIDER", "groq").lower()

        # Cấu hình chính dựa trên provider
        if self.provider == "groq" and (api_key or settings.GROQ_API_KEY):
            self.api_key = api_key or settings.GROQ_API_KEY
            self.base_url = base_url or settings.GROQ_BASE_URL
            self.model = model or settings.GROQ_MODEL
        else:
            self.api_key = api_key or settings.OPENROUTER_API_KEY
            self.base_url = base_url or settings.OPENROUTER_BASE_URL
            self.model = model or settings.OPENROUTER_MODEL

        self.site_url = settings.OPENROUTER_SITE_URL
        self.app_name = settings.OPENROUTER_APP_NAME

        default_headers = {}
        if self.site_url:
            default_headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            default_headers["X-Title"] = self.app_name

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers=default_headers if default_headers else None,
            timeout=30.0,
        )

    def generate(
        self,
        messages: List[dict],
        temperature: float = 0.2,
        max_tokens: int = 600,
    ) -> str:
        """Gửi prompt và nhận câu trả lời từ LLM với cơ chế bắt lỗi thân thiện."""
        try:
            logger.info(f"Gửi request tới LLM ({self.provider} - Model: {self.model})")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as e:
            err_str = str(e)
            logger.error(f"Lỗi khi gọi LLM API ({self.provider}): {err_str}")
            if "429" in err_str or "Rate limit" in err_str:
                return (
                    f"⚠️ Dịch vụ mô hình ngôn ngữ ({self.provider}) tạm thời đạt giới hạn số lượt gọi. "
                    "Các tầng tìm kiếm pháp lý (BM25 + Qdrant Vector) vẫn hoạt động bình thường bên dưới."
                )
            return f"⚠️ Dịch vụ mô hình ngôn ngữ gặp sự cố tạm thời: {err_str}"
