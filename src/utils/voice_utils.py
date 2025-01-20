from tts.models import build_model
from tts.kokoro import generate

import torch
from typing import Tuple

class VoiceUtils:
    def __init__(self) -> None:
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.MODEL = build_model('./src/tts/kokoro-v0_19-half.pth', self.device)
        self.VOICEPACK = torch.load(f'./src/tts/af_bella.pt', weights_only=True).to(self.device)

    async def generate_voice(self, text: str) -> Tuple[torch.Tensor, str]:
        audio, out_ps = generate(self.MODEL, text, self.VOICEPACK, lang='a')
        return audio, out_ps