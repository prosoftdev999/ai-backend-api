from dataclasses import dataclass
from typing import Any

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

from app.core.config import settings


SYSTEM_INSTRUCTIONS = (
    "You are a helpful assistant inside an AI backend API. "
    "Answer accurately and clearly. "
    "Do not claim knowledge that is not present in the conversation. "
    "When uncertain, state that clearly."
)


@dataclass(slots=True)
class LLMMessage:
    role: str
    content: str


class LLMServiceError(Exception):
    """Base exception for LLM service failures."""


class LLMAuthenticationError(LLMServiceError):
    """Raised when the provider rejects the API key."""


class LLMRateLimitError(LLMServiceError):
    """Raised when the provider rate limit or quota is exceeded."""


class LLMRequestError(LLMServiceError):
    """Raised when the provider rejects a request."""


class LLMConnectionError(LLMServiceError):
    """Raised when the provider cannot be reached."""


class LLMService:
    def __init__(self) -> None:
        timeout = httpx.Timeout(
            timeout=settings.llm_timeout_seconds,
            connect=15.0,
        )

        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=timeout,
            max_retries=2,
        )

    @staticmethod
    def _build_input(messages: list[LLMMessage]) -> list[dict[str, Any]]:
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

    async def generate_reply(
        self,
        messages: list[LLMMessage],
    ) -> str:
        if not messages:
            raise LLMRequestError("At least one message is required.")

        try:
            response = await self.client.responses.create(
                model=settings.llm_model,
                instructions=SYSTEM_INSTRUCTIONS,
                input=self._build_input(messages),
                max_output_tokens=settings.llm_max_output_tokens,
            )

            output_text = response.output_text.strip()

            if not output_text:
                raise LLMServiceError(
                    "The language model returned an empty response."
                )

            return output_text

        except AuthenticationError as exc:
            raise LLMAuthenticationError(
                "The LLM API key is invalid or unauthorized."
            ) from exc

        except RateLimitError as exc:
            raise LLMRateLimitError(
                "The LLM provider rate limit or account quota was exceeded."
            ) from exc

        except BadRequestError as exc:
            raise LLMRequestError(
                f"The LLM provider rejected the request: {exc.message}"
            ) from exc

        except APITimeoutError as exc:
            raise LLMConnectionError(
                "The request to the LLM provider timed out."
            ) from exc

        except APIConnectionError as exc:
            raise LLMConnectionError(
                "Could not connect to the LLM provider."
            ) from exc

        except APIStatusError as exc:
            raise LLMServiceError(
                f"The LLM provider returned HTTP {exc.status_code}."
            ) from exc

    async def close(self) -> None:
        await self.client.close()


llm_service = LLMService()