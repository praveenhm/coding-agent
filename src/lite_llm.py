"""LiteLLM Framework for OpenAI Compatibility
This module provides a unified interface for interacting with various LLM providers
through the LiteLLM framework, maintaining compatibility with the OpenAI API.
"""

import os
from typing import Any, Dict, List, Optional, Union

import openai  # type: ignore
from litellm import completion, completion_cost  # type: ignore


class LiteLLMClient:
    """A client for interacting with various LLM providers through the LiteLLM framework.

    This class provides a unified interface that's compatible with the OpenAI API,
    making it easy to switch between different LLM providers without changing your code.
    """

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 10.0,
        max_retries: int = 2,
        temperature: float = 0.7,
        **kwargs,
    ):
        """Initialize the LiteLLM client.

        Args:
            model: The name of the model to use (e.g., "gpt-3.5-turbo", "claude-instant-1")
            api_base: The base URL for the API endpoint
            api_key: The API key for authentication
            timeout: Timeout in seconds for API requests
            max_retries: Maximum number of retries for failed requests
            temperature: Temperature setting for the model
            **kwargs: Additional keyword arguments to pass to the LiteLLM client
        """
        self.model = model
        self.api_base = api_base or os.getenv("LITELLM_API_BASE")
        self.api_key = api_key or os.getenv("LITELLM_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries
        self.temperature = temperature
        self.kwargs = kwargs  # Store kwargs as an instance variable

        # Set default API key if not provided
        if not self.api_key and "openai" in model.lower():
            self.api_key = os.getenv("OPENAI_API_KEY")

        # Configure LiteLLM with OpenAI compatibility
        openai.api_base = self.api_base or "https://api.openai.com/v1"
        openai.api_key = self.api_key or ""

    def chat_completion(
        self, messages: List[Dict[str, str]], stream: bool = False, **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Generate a response using the specified model.

        Args:
            messages: A list of message dictionaries with 'role' and 'content'
            stream: Whether to use streaming mode
            **kwargs: Additional arguments to pass to the completion function

        Returns:
            The completion result from LiteLLM or OpenAI
        """
        try:
            # Use LiteLLM's completion function which supports multiple providers
            response = completion(
                model=self.model,
                messages=messages,
                api_base=self.api_base,
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
                temperature=self.temperature,
                stream=stream,
                **kwargs,
            )

            # Calculate cost if available
            if hasattr(response, "usage"):
                response.cost = completion_cost(
                    model=self.model,
                    messages=messages,
                    api_base=self.api_base,
                    api_key=self.api_key,
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                    temperature=self.temperature,
                    stream=stream,
                    **kwargs,
                )

            return response

        except Exception as e:
            # Fall back to OpenAI's native implementation if applicable
            if "openai" in self.model.lower():
                try:
                    openai_response = openai.ChatCompletion.create(
                        model=self.model, messages=messages, temperature=self.temperature, stream=stream, **kwargs
                    )
                    return openai_response
                except Exception as e2:
                    error_msg = f"LiteLLM failed: {str(e)}. OpenAI fallback also failed: {str(e2)}"
                    raise RuntimeError(error_msg) from e2
            else:
                raise RuntimeError(f"LiteLLM failed for model {self.model}: {str(e)}") from e

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.

        Returns:
            A dictionary containing model information
        """
        return {
            "model": self.model,
            "api_base": self.api_base,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "kwargs": self.kwargs,
        }

    def set_model(self, model: str) -> None:
        """Set a new model to use.

        Args:
            model: The name of the model to use (e.g., "gpt-3.5-turbo", "claude-instant-1")
        """
        self.model = model

    def set_temperature(self, temperature: float) -> None:
        """Set a new temperature value.

        Args:
            temperature: The new temperature value
        """
        self.temperature = temperature


if __name__ == "__main__":

    def example_usage():
        """Example usage of the LiteLLM client."""

        # Initialize the client
        client = LiteLLMClient(model="gpt-3.5-turbo", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)

        # Create a message history
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain how LiteLLM works."},
        ]

        # Get completion
        response = client.chat_completion(messages)

        if isinstance(response, dict):
            print(f"Response: {response['choices'][0]['message']['content']}")
            if "cost" in response:
                print(f"Cost: ${response['cost']:.6f}")
        elif isinstance(response, list):
            for chunk in response:
                print(chunk.choices[0].delta.content or "", end="", flush=True)

        # Get model info
        print("\nModel Info:", client.get_model_info())

    example_usage()
