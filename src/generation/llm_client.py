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

        # Làm sạch API key (tránh khoảng trắng hoặc ký tự lỗi khi copy-paste vào Secrets)
        self.api_key = (self.api_key or "").strip()

        default_headers = {}
        if self.site_url and self.site_url.isascii():
            default_headers["HTTP-Referer"] = self.site_url.strip()
        if self.app_name and self.app_name.isascii():
            default_headers["X-Title"] = self.app_name.strip()

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers=default_headers if default_headers else None,
            timeout=30.0,
        )

    # Danh sách model dự phòng trên Groq khi model chính chạm giới hạn tốc độ (429)
    GROQ_FALLBACK_MODELS = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]

    def generate(
        self,
        messages: List[dict],
        temperature: float = 0.2,
        max_tokens: int = 350,
    ) -> str:
        """Gửi prompt và nhận câu trả lời từ LLM với cơ chế tự động xoay vòng model dự phòng khi chạm rate limit."""
        if not self.api_key:
            return "⚠️ Dịch vụ mô hình ngôn ngữ chưa được cấu hình API Key."

        models_to_try = [self.model]
        if self.provider == "groq":
            for m in self.GROQ_FALLBACK_MODELS:
                if m not in models_to_try:
                    models_to_try.append(m)

        last_err = ""
        for model_name in models_to_try:
            try:
                logger.info(f"Gửi request tới LLM ({self.provider} - Model: {model_name})")
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content or ""
                if content.strip():
                    return content.strip()
            except Exception as e:
                last_err = str(e)
                logger.warning(f"Model {model_name} gặp lỗi: {last_err}")
                if "401" in last_err or "Invalid API Key" in last_err:
                    break
                continue

        logger.error(f"Tất cả các model LLM ({self.provider}) đều thất bại: {last_err}")
        if "429" in last_err or "Rate limit" in last_err:
            return (
                f"⚠️ Dịch vụ mô hình ngôn ngữ ({self.provider}) tạm thời đạt giới hạn số lượt gọi. "
                "Vui lòng thử lại sau vài giây."
            )
        return f"⚠️ Dịch vụ mô hình ngôn ngữ gặp sự cố tạm thời: {last_err}"
