import logging
import zenoh
from pydantic import Field
from typing import Optional

from actions.base import ActionConfig, ActionConnector
from actions.speak.interface import SpeakInput
from zenoh_msgs import open_zenoh_session

class PersonaPlexSpeakerConfig(ActionConfig):
    """
    Configuration for PersonaPlex Speaker Connector.
    Receives audio from Zenoh (PersonaPlex fork) and plays it.
    """
    topic: str = Field(default="pepper/audio/speaker", description="Zenoh topic for speaker audio")

class PersonaPlexSpeakerConnector(ActionConnector[PersonaPlexSpeakerConfig, SpeakInput]):
    """
    Subscribes to audio from PersonaPlex via Zenoh and plays it on Pepper.
    """
    def __init__(self, config: PersonaPlexSpeakerConfig):
        super().__init__(config)
        self.session = open_zenoh_session()
        # Publisher to send text-to-speech to PersonaPlex if needed
        self.text_pub = self.session.declare_publisher(self.config.topic + "/text")
        logging.info(f"PersonaPlex Speaker Proxy ready on {self.config.topic}")

    async def connect(self, output_interface: SpeakInput) -> None:
        """
        When the LLM (System 2) wants Pepper to speak.
        We send the text to PersonaPlex so it can generate the audio with its voice.
        """
        text = output_interface.action
        logging.info(f"Sending text to PersonaPlex Speaker: {text}")
        
        # Publish to PersonaPlex so it verbalizes the System 2 reasoning
        self.text_pub.put(text)
        
        # We don't need to 'play' anything here if PersonaPlex handles audio.
        # But this method being called ensures WebSim shows 'Speaking: ...'
        pass

