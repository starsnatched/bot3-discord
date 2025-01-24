from txtai.pipeline import TextToSpeech

import torch
from typing import Tuple

class VoiceUtils:
    def __init__(self) -> None:
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.tts = TextToSpeech("NeuML/kokoro-int8-onnx")

    async def generate_voice(self, text: str) -> Tuple[torch.Tensor, str]:
        audio, out_ps = self.tts(text)
        return audio, out_ps