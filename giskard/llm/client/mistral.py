from typing import Optional, Sequence

from dataclasses import asdict

from ..config import LLMConfigurationError
from ..errors import LLMImportError
from . import LLMClient
from .base import ChatMessage

try:
    from mistralai.client import MistralClient as _MistralClient
    from mistralai.models.chat_completion import ChatMessage as MistralChatMessage
except ImportError as err:
    raise LLMImportError(flavor="llm") from err


class MistralClient(LLMClient):
    def __init__(self, model: str = "mistral-large-latest", client: _MistralClient = None):
        self.model = model
        self._client = client or _MistralClient()

    def complete(
        self,
        messages: Sequence[ChatMessage],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        caller_id: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> ChatMessage:
        extra_params = dict()
        if seed is not None:
            extra_params["random_seed"] = seed

        try:
            completion = self._client.chat(
                model=self.model,
                messages=[MistralChatMessage(**asdict(m)) for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params,
            )
        except RuntimeError as err:
            raise LLMConfigurationError("Could not get response from Mistral API") from err

        self.logger.log_call(
            prompt_tokens=completion.usage.prompt_tokens,
            sampled_tokens=completion.usage.completion_tokens,
            model=self.model,
            client_class=self.__class__.__name__,
            caller_id=caller_id,
        )

        msg = completion.choices[0].message

        return ChatMessage(role=msg.role, content=msg.content)