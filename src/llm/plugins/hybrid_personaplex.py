import logging
import typing as T
import json
from pydantic import Field

from llm import LLM, LLMConfig
from llm.output_model import Action, CortexOutputModel
from zenoh_msgs import open_zenoh_session

class HybridPersonaPlexConfig(LLMConfig):
    """
    Configuration for Hybrid PersonaPlex + OpenAI Brain.
    """
    openai_model: str = Field(default="gpt-4", description="Model for deep reasoning")
    personaplex_topic: str = Field(default="pepper/personaplex/control", description="Zenoh topic to talk to PersonaPlex")

class HybridPersonaPlexLLM(LLM):
    """
    The Orchestrator.
    Manages the persona (Moshi) for quick talk and OpenAI for heavy thinking.
    """
    def __init__(self, config: HybridPersonaPlexConfig):
        super().__init__(config)
        self.session = open_zenoh_session()
        self.control_pub = self.session.declare_publisher(self.config.personaplex_topic)
        logging.info("Hybrid PersonaPlex Orchestrator initialized")

    async def ask(self, messages: T.List[T.Dict[str, str]], **kwargs) -> T.Optional[CortexOutputModel]:
        """
        Decision loop:
        1. Analyze user intention.
        2. If complex -> Call OpenAI in background, tell PersonaPlex to say 'thinking...'.
        3. If simple -> Let PersonaPlex handle it.
        """
        last_message = messages[-1]["content"] if messages else ""
        
        # LOGIC: Check if it requires deep reasoning
        if "calcula" in last_message.lower() or "razona" in last_message.lower():
            # Tactic: Send immediate command to PersonaPlex via Zenoh to make it talk (System 1)
            self.control_pub.put(json.dumps({
                "command": "generate_filler",
                "type": "thinking"
            }))
            
            # Tactic: Call OpenAI for the real answer (System 2)
            # (Note: You would use an OpenAI client here)
            logging.info("Deep reasoning triggered for: " + last_message)
            
            # Return a placeholder or the result once ready
            return CortexOutputModel(actions=[Action(type="speak", value="Estoy analizando eso con cuidado...")])
            
        return None
