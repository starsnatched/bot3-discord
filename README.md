# Usage
Download the TTS model:

```
cd src/tts

wget https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/fp16/kokoro-v0_19-half.pth
```

Install requirements:

```
pip install -r requirements.txt
```

Configure .env:

```
# Discord
DISCORD_TOKEN=
DEV_ID=YOUR_DISCORD_USER_ID

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=smallthinker
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_NUM_CTX=32000

# Misc
BACKEND_TYPE=ollama
```

Have fun!
```
python src/bot.py
```

You need to ping the bot in your guild for it to respond.

# Adding More Tools
Within `src/utils/models.py`, add a `BaseToolArgs` class as such:

```python
class DiceRoll(BaseToolArgs):
    """A tool to roll a dice."""
    tool_type: Literal["dice_roll"]
    sides: int = Field(..., description="Number of sides on the dice to roll.")
```

Then, add the name of the class into the `ToolArgs` array:

```python
ToolArgs = Union[
    SendMessage,
    SendVoiceMessage,
    MemoryInsert,
    MemoryRetrieve,
    DiceRoll # append it here
]
```

Go to `src/utils/discord_utils.py`, within `handle_tools` method, write a handler for the tool:

```python
if output.tool_args.tool_type == "dice_roll":
    result = random.randint(1, output.tool_args.sides)
    return self.create_tool_return_json(output.tool_args.tool_type, result)
```

You only need to make it return the JSON string back, so the `ai_chat` cog can handle the response automatically.

# Features
It can currently do:
- Store/retrieve information in its long-term memory.
- Send a text message.
- Chain multiple tools/messages.
- Send a voice message.
- Roll a dice!