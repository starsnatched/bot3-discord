# Usage
### *The approximate total system RAM/VRAM you need is <20GB, IF you're using local Ollama. If you use cloud-hosted services or OpenAI API, the RAM/VRAM cost is much lower at <500MB.*

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
OLLAMA_MODEL=deepseek-r1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_NUM_CTX=64000

# Misc
BACKEND_TYPE=ollama
PERSONA="A deep thinker named bot3. You always reply with one short sentence."
```

Have fun!
```
python src/bot.py
```

# Commands
Toggle AI chatbot in the channel:

```
/toggle
```

However, the bot will respond when it's pinged, even if it's toggled off. To prevent that, use:

```
/disable #channel_name
```

This will make the bot completely ignore the specified channel. To re-enable:

```
/enable
```

To see if the bot is enabled in the channel:

```
/status
```

If you believe you messed up, or if the LLM is acting up, run:

```
/reset
```

This will reset the chat history in the specific channel.

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
    # Optional: Send a debugging message that only the developer can trigger.
    if message.author.id == self.bot.dev_id:
        await message.reply(f"-# Calling tool: {output.tool_args.tool_type}", mention_author=False, view=ButtonView(output.reasoning, self.bot.dev_id))
    result = random.randint(1, output.tool_args.sides)
    return self.create_tool_return_json(output.tool_args.tool_type, result)
```

You only need to make it return the JSON string back, so the `ai_chat` cog can handle the response automatically.

# Features
It can currently do:
- Perform an o1-like reasoning before taking an action, resulting in much higher quality of outputs.
- Store/retrieve information in its long-term memory.
- Send a text message.
- Chain multiple tools/messages.
- Send a voice message.
- Roll a dice!

# [Ollama](https://ollama.com) Usage
You can also use this with [Ollama](https://ollama.com), if you wish to run everything locally.

After installing Ollama, run:
```
ollama pull deepseek-r1:8b
ollama pull nomic-embed-text
```

NOTE: Only "native thinker" models work well with this Discord bot for now. Currently the best thinker model is `deepseek-r1`.

The model `deepseek-r1:8b (4.9GB)` can be ran on any device with ~18GB of available RAM/VRAM (at 64,000 token context window). It runs really fast on a CPU. The LLM performs surprisingly well for its size, and is highly reliable. You will also need more RAM/VRAM for the Text-to-Speech model, as well as the embedding model. Both of them are really small, so you don't need a lot more to run those.

Also no data is collected to train the model, so it's a great piece of mind.

I have set the context window to 64,000. However, you can increase this up to 131,072. If you do so, the LLM will consume a lot more RAM/VRAM, and the quality of the output will degrade.

Then, change `.env` as such:

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_NUM_CTX=64000

BACKEND_TYPE=ollama
```

Have fun!

```
python src/bot.py
```

# Personality Injection
You may inject a personality prompt, which can be as detailed as you want, into the LLM:

```
PERSONA="A deep thinker named bot3. You always reply with one short sentence."
```

Whether the LLM will be good at following your persona prompt depends on its capabilities.