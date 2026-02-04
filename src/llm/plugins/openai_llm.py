import json
import logging
import re
import time
import typing as T
from enum import Enum

import openai
from pydantic import BaseModel, Field

from llm import LLM, LLMConfig
from llm.function_schemas import convert_function_calls_to_actions
from llm.output_model import Action, CortexOutputModel
from providers.avatar_llm_state_provider import AvatarLLMState
from providers.llm_history_manager import LLMHistoryManager

R = T.TypeVar("R", bound=BaseModel)


class OpenAIModel(str, Enum):
    """Available OpenAI models."""

    GPT_4_O = "gpt-4o"
    GPT_4_O_MINI = "gpt-4o-mini"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"


class OpenAIConfig(LLMConfig):
    """OpenAI-specific configuration with model enum."""

    base_url: T.Optional[str] = Field(
        default="https://api.openmind.org/api/core/openai",
        description="Base URL for the OpenAI API endpoint",
    )
    model: T.Optional[T.Union[OpenAIModel, str]] = Field(
        default=OpenAIModel.GPT_4_1_MINI,
        description="OpenAI model to use",
    )
    # Added API key field to allow authentication with custom endpoints (e.g., vLLM)
    api_key: T.Optional[str] = Field(
        default=None,
        description="API key or token for the OpenAI-compatible endpoint",
    )
    # Timeout for the HTTP request (seconds). Allows the client to fail fast if the service is unresponsive.
    timeout: T.Optional[float] = Field(
        default=30.0,
        description="Request timeout in seconds for the OpenAI API calls",
    )


class OpenAILLM(LLM[R]):
    """
    An OpenAI-based Language Learning Model implementation with function call support.

    This class implements the LLM interface for OpenAI's GPT models, handling
    configuration, authentication, and async API communication. It supports both
    traditional JSON structured output and function calling.
    """

    def __init__(
        self,
        config: OpenAIConfig,
        available_actions: T.Optional[T.List] = None,
    ):
        """
        Initialize the OpenAI LLM instance.

        Parameters
        ----------
        config : OpenAILLMConfig, optional
            Configuration settings for the LLM.
        available_actions : list[AgentAction], optional
            List of available actions for function calling.
        """
        super().__init__(config, available_actions)

        if not config.api_key:
            raise ValueError("config file missing api_key")
        if not config.model:
            self._config.model = "gpt-4.1-mini"

        self._client = openai.AsyncClient(
            base_url=config.base_url or "https://api.openmind.org/api/core/openai",
            api_key=config.api_key,
        )

        # Initialize history manager
        self.history_manager = LLMHistoryManager(self._config, self._client)

    @AvatarLLMState.trigger_thinking()
    @LLMHistoryManager.update_history()
    async def ask(
        self, prompt: str, messages: T.List[T.Dict[str, str]] = []
    ) -> T.Optional[R]:
        """
        Send a prompt to the OpenAI API and get a structured response.

        Parameters
        ----------
        prompt : str
            The input prompt to send to the model.
        messages : List[Dict[str, str]]
            List of message dictionaries to send to the model.

        Returns
        -------
        R or None
            Parsed response matching the output_model structure, or None if
            parsing fails.
        """
        try:
            logging.info(f"OpenAI input: {prompt}")
            logging.info(f"OpenAI messages: {messages}")

            self.io_provider.llm_start_time = time.time()
            self.io_provider.set_llm_prompt(prompt)

            formatted_messages = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in messages
            ]
            formatted_messages.append({"role": "user", "content": prompt})

            response = await self._client.chat.completions.create(
                model=self._config.model or "gpt-5",
                messages=T.cast(T.Any, formatted_messages),
                tools=T.cast(T.Any, self.function_schemas),
                tool_choice="auto",
                timeout=self._config.timeout,
            )

            if not response.choices:
                logging.warning("OpenAI API returned empty choices")
                return None

            message = response.choices[0].message
            self.io_provider.llm_end_time = time.time()

            # Handle native tool calls first
            if message.tool_calls:
                logging.info(f"Received {len(message.tool_calls)} function calls")
                function_call_data = [
                    {
                        "function": {
                            "name": getattr(tc, "function").name,
                            "arguments": getattr(tc, "function").arguments,
                        }
                    }
                    for tc in message.tool_calls
                ]
                actions = convert_function_calls_to_actions(function_call_data)
                return T.cast(R, CortexOutputModel(actions=actions))

            # Fallback for OSS models that return structured text or JSON in content
            content = message.content
            if not content:
                logging.warning("OpenAI API returned empty choices and content")
                return None

            logging.info(f"Parsing fallback content: {content}")
            actions = []

            # Map common keys to actual action types (llm_label)
            # In spot.json5: move -> move, speak -> speak, face -> emotion
            mapping = {
                "move": "move",
                "action": "move",
                "command": "move",
                "speak": "speak",
                "text": "speak",
                "message": "speak",
                "emotion": "emotion",
                "face": "emotion",
                "mood": "emotion"
            }

            # Try to parse as JSON first
            try:
                import json
                # Try to find JSON block in case there's preamble/postamble
                json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    data = json.loads(json_str)
                    
                    # Normalize data to a list of dicts
                    candidates = []
                    if isinstance(data, list):
                        candidates = data
                    elif isinstance(data, dict):
                        if "actions" in data and isinstance(data["actions"], list):
                            candidates = data["actions"]
                        else:
                            candidates = [data]
                    
                    for item in candidates:
                        if not isinstance(item, dict):
                            continue
                            
                        if "type" in item and "value" in item:
                            actions.append(Action(type=mapping.get(str(item["type"]).lower(), str(item["type"])), value=str(item["value"])))
                            continue
                        
                        found_mapped = False
                        for key, action_type in mapping.items():
                            if key in item:
                                actions.append(Action(type=action_type, value=str(item[key])))
                                found_mapped = True
                                break
                        
                        if not found_mapped and item:
                            first_key = list(item.keys())[0]
                            actions.append(Action(type=mapping.get(first_key.lower(), first_key), value=str(item[first_key])))
            except Exception as e:
                logging.debug(f"JSON fallback parsing failed: {e}")

            # If JSON parsing failed or yielded no actions, try regex for "Key: Value" format
            if not actions:
                # Match "Move: sit", "Speak: {{hello}}", "Emotion: 'joy'" etc.
                # Updated regex to better handle quotes and avoid trailing punctuation
                patterns = [
                    r"(?i)(Move|Speak|Emotion|face|action)\s*:\s*(?:\{\{)?\s*['\"]?(.*?)['\"]?\s*(?:\}\})?(?=\s*[,;]|\n|$)",
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                    for match in matches:
                        raw_type = match.group(1).lower()
                        action_type = mapping.get(raw_type, raw_type)
                        value = match.group(2).strip()
                        # Strip trailing quote if only leading quote was matched
                        if value.endswith("'") or value.endswith('"'):
                            value = value[:-1]
                        actions.append(Action(type=action_type, value=value))

            if actions:
                logging.info(f"Extracted {len(actions)} actions: {actions}")
                return T.cast(R, CortexOutputModel(actions=actions))

            # If no actions found, treat as a pure speech response if there is content
            if content.strip():
                actions.append(Action(type="speak", value=content.strip()))
                return T.cast(R, CortexOutputModel(actions=actions))

            return None

        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return None
