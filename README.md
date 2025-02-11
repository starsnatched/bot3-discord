# Usage
### *The approximate total system RAM/VRAM you need is <12GB, IF you're using local Ollama. If you use cloud-hosted services or OpenAI API, the RAM/VRAM cost is much lower at <200MB.*

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
OLLAMA_MODEL=huihui_ai/deepseek-r1-abliterated:14b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_NUM_CTX=32000

# Misc
BACKEND_TYPE=ollama
PERSONA="A deep thinker named bot3."
NAME=bot3
SERVER=Euphoria
```

Have fun!
```
python src/bot.py
```

# Commands
All commands are prefixed with `/ai`

### Basic Commands

| Command | Description |
|---------|-------------|
| `/ai toggle` | Toggles AI chat on/off in the current channel |
| `/ai enable` | Enables AI chat in the current channel |
| `/ai disable` | Disables AI chat in the current channel |
| `/ai status` | Shows the current AI status in the channel |
| `/ai reset` | Clears the chat history |

### Tool Management

| Command | Description |
|---------|-------------|
| `/ai tools` | Lists all available AI tools |
| `/ai enable_tool <tool>` | Enables a specific tool |
| `/ai disable_tool <tool>` | Disables a specific tool |

## Usage Examples

### Channel Management

Enable AI in a channel:
```
/ai enable
```

Disable AI in a channel:
```
/ai disable [channel]  # Optional channel parameter
```

Check AI status:
```
/ai status
```

Clear chat history:
```
/ai reset
```

### Tool Management

List available tools:
```
/ai tools
```

Enable a specific tool:
```
/ai enable_tool <tool_name>
```

Disable a tool:
```
/ai disable_tool <tool_name>
```

### Permissions

- Commands that modify settings (`toggle`, `enable`, `disable`, `reset`, `enable_tool`, `disable_tool`) require "Manage Messages" permission
- Status and tools list can be viewed by all users

### Chat Behavior

- Bot responds to messages in enabled channels
- In other channels, bot only responds when mentioned
- Image uploads are supported only in OpenAI mode (max 20MB)
- Message edits are processed in real-time
- Tool `send_message` cannot be disabled

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
- React to a message.
- Generate an image (not implemented on Ollama backend yet).
- Roll a dice!

# [Ollama](https://ollama.com) Usage
You can also use this with [Ollama](https://ollama.com), if you wish to run everything locally.

After installing Ollama, run:
```
ollama pull huihui_ai/deepseek-r1-abliterated:14b
ollama pull nomic-embed-text
```

NOTE: Only "native thinker" models work well with this Discord bot for now. Currently the best thinker model for this Discord bot is `huihui_ai/deepseek-r1-abliterated:14b`.

You may find other "native thinker" models [here](https://ollama.com/library/deepseek-r1). The required RAM/VRAM for each model can be approximated using: size of the .gguf file + ~25% (for kv cache). For `huihui_ai/deepseek-r1-abliterated:14b`, it has .gguf file size of 9GB, with KV cache size of about 2GB, making the memory requirement to 11GB. Transformer models' KV cache scales quadratically, based on your set `num_ctx`, or context window. Lower than 32,000 token window will consume less than 25% of the original model's size, and more than 64,000 will consume more than that ratio.

The model `huihui_ai/deepseek-r1-abliterated:14b (9GB)` can be ran on any device with ~11GB of available RAM/VRAM (at 32,000 token context window). It runs really fast on a CPU. The LLM performs surprisingly well for its size, and is highly reliable. You will also need more RAM/VRAM for the Text-to-Speech model, as well as the embedding model. Both of them are really small, so you don't need a lot more to run those.

Model `huihui_ai/deepseek-r1-abliterated:14b` is "abliterated," which means the LLM's ability to represent the refusal direction has been removed, essentially means it's uncensored. It'll answer NSFW, or harmful prompts, without refusing.

Also no data is collected to train the model, so it's a great piece of mind.

Then, change `.env` as such:

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=huihui_ai/deepseek-r1-abliterated:14b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_NUM_CTX=32000

BACKEND_TYPE=ollama
```

Have fun!

```
python src/bot.py
```

# Personality Injection
You may inject a personality prompt, which can be as detailed as you want, into the LLM:

```
PERSONA="A deep thinker named bot3."
NAME=bot3
```

Whether the LLM will be good at following your persona prompt depends on its capabilities.