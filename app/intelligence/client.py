import logging
from enum import Enum
from typing import TypeVar

import instructor
import openai
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class Models(Enum):
    """Available language models."""

    GPT4o_MINI = "gpt-4o-mini"
    GPT4o = "gpt-4o"
    GPT35_TURBO = "gpt-3.5-turbo"


class EmbeddingModels(Enum):
    """Available embedding models."""

    TEXT_EMBED_3_SMALL = "text-embedding-3-small"
    TEXT_EMBED_3_LARGE = "text-embedding-3-large"


class LLMClient:
    def __init__(self, debug: bool = False) -> None:
        self.client = openai.OpenAI()
        self.debug = debug

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        model: Models = Models.GPT4o_MINI,
        temperature: float | None = None,
    ) -> tuple[ChatCompletion, str]:
        try:
            if self.debug:
                logger.debug(f"Sending request to {model.value}")
                logger.debug(f"Messages: {messages}")

            if temperature is not None:
                kwargs = {
                    "temperature": temperature,
                }
            else:
                kwargs = {}

            response = self.client.chat.completions.create(
                model=model.value,
                messages=messages,  # type: ignore
                **kwargs,
            )

            if self.debug:
                logger.debug(f"Response received: {response}")

            return response, response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"Error from LLM - OpenAI: {e}")
            raise e

    async def extract_structured_data(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        model: Models = Models.GPT4o_MINI,
    ) -> T:
        try:
            if self.debug:
                logger.debug(f"Extracting structured data using {model.value}")
                logger.debug(f"Messages: {messages}")
                logger.debug(f"Schema: {schema}")

            structured_extraction_client = instructor.from_openai(self.client)
            response = structured_extraction_client.chat.completions.create(
                model=model.value,
                messages=messages,  # type: ignore
                response_model=schema,
            )

            if self.debug:
                logger.debug(f"Structured response received: {response}")

            return response

        except Exception as e:
            logger.error(f"Error from LLM - OpenAI: {e}")
            raise e

    async def generate_embedding(
        self,
        text: str,
        model: EmbeddingModels = EmbeddingModels.TEXT_EMBED_3_SMALL,
    ) -> list[float]:
        try:
            response = self.client.embeddings.create(
                model=model.value,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error from LLM - OpenAI: {e}")
            raise e
