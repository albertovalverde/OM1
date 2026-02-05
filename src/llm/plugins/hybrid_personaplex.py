import logging
import typing as T
import json
from pydantic import Field

from llm import LLM, LLMConfig
from llm.output_model import Action, CortexOutputModel
from zenoh_msgs import open_zenoh_session

from llm.plugins.openai_llm import OpenAILLM, OpenAIConfig

class HybridPersonaPlexConfig(OpenAIConfig):
    """
    Configuration for Hybrid PersonaPlex + OpenAI Brain.
    """
    personaplex_topic: str = Field(default="pepper/personaplex/control", description="Zenoh topic to talk to PersonaPlex")

class HybridPersonaPlexLLM(OpenAILLM):
    """
    The Orchestrator.
    Manages the persona (Moshi) for quick talk and OpenAI for heavy thinking.
    """
    def __init__(self, config: HybridPersonaPlexConfig, available_actions: T.Optional[T.List] = None):
        super().__init__(config, available_actions)
        self.session = open_zenoh_session()
        self.control_pub = self.session.declare_publisher(self._config.personaplex_topic)
        logging.info("Hybrid PersonaPlex Orchestrator initialized (System 1/2)")


    async def ask(self, prompt: str, messages: T.List[T.Dict[str, str]] = []) -> T.Optional[CortexOutputModel]:
        """
        Decision loop:
        1. If it's a deep query -> Send 'thinking' to PersonaPlex and call OpenAI.
        2. Otherwise -> Let PersonaPlex handle it (be silent in OM1 context).
        """
        # Detection of complex queries (simplified)
        deep_keywords = ["calcula", "razona", "explica", "distancia", "por qué", "qué es"]
        is_deep = any(kw in prompt.lower() for kw in deep_keywords)

        if is_deep:
            logging.info(f"System 2 (Deep Reasoning) triggered for: {prompt}")
            
            # Send immediate filler to PersonaPlex via Zenoh
            self.control_pub.put(json.dumps({
                "command": "thinking_filler",
                "text": "Déjame pensar un segundo sobre eso..."
            }))
            
            # Use OpenAI for the heavy lifting
            return await super().ask(prompt, messages)
        
        # If simple, we stay silent to let Moshi (System 1) handle the verbal interaction
        logging.info(f"System 1 (PersonaPlex) handling: {prompt}")
        return None

