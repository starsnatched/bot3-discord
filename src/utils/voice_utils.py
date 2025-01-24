from txtai.pipeline import TextToSpeech

import torch
from typing import Tuple

class VoiceUtils:
    def __init__(self) -> None:
        self.tts = TextToSpeech("NeuML/kokoro-fp16-onnx")

    async def generate_voice(self, text: str) -> Tuple[torch.Tensor, str]:
        audio, out_ps = self.tts(text, speaker="af_bella")
        return audio, out_ps