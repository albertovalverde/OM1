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
    Also handles "Barge-in" (interrupting Pepper's speech).
    """
    def __init__(self, config: PersonaPlexSpeakerConfig):
        super().__init__(config)
        self.session = open_zenoh_session()
        self.subscriber = self.session.declare_subscriber(self.config.topic, self._on_audio_data)
        logging.info(f"PersonaPlex Speaker Proxy listening on {self.config.topic}")

    def _on_audio_data(self, sample):
        # Handle incoming audio chunk from PersonaPlex
        # This is where you would play it via Pepper's ALAudioPlayer or similar.
        pass

    async def connect(self, output_interface: SpeakInput) -> None:
        # This is called if the LLM sends a 'speak' action.
        # In a full-duplex setup, audio often flows directly from Zenoh.
        # However, we can use this to send "text interventions" to PersonaPlex.
        pass
