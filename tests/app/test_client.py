from unittest.mock import MagicMock

import pytest
from _pytest.config import Config
from pydantic import BaseModel

from app.client import LLMClient


# Sample Pydantic model for testing structured data extraction
class SampleSchema(BaseModel):
    name: str
    age: int


@pytest.fixture
def mock_openai_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(mock_openai_client: MagicMock) -> LLMClient:
    client = LLMClient()
    client.client = mock_openai_client
    return client


def pytest_configure(config: Config) -> None:
    """Add custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test that makes real API calls",
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_generate_response() -> None:
    """Integration test making real API calls. Skip by default."""
    # Arrange
    client = LLMClient()
    messages = [{"role": "user", "content": "What is 2+2?"}]

    # Act
    response, content = await client.generate_response(messages)

    # Assert
    assert content is not None
    assert len(content) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_extract_structured_data() -> None:
    """Integration test making real API calls. Skip by default."""
    # Arrange
    client = LLMClient()
    messages = [
        {"role": "user", "content": "Extract this data: Name is John Smith, age is 30"}
    ]

    # Act
    result = await client.extract_structured_data(messages, SampleSchema)

    # Assert
    assert isinstance(result, SampleSchema)
    assert result.name
    assert result.age > 0
