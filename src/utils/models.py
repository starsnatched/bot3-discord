from pydantic import BaseModel, Field, field_validator
from typing import Literal, Union, Type

class BaseToolArgs(BaseModel):
    """Base class for all tool arguments."""
    tool_type: str = Field(..., description="Type of the tool being used.")

# Basic tool classes
class SendMessage(BaseToolArgs):
    """A tool to send a message to the user. Make it short and concise, and if you need to send a long message, split it into multiple messages using `call_another_tool`."""
    tool_type: Literal["send_message"]
    content: str = Field(..., description="Content of the message to send. Make it short and concise.")
    call_another_tool: bool = Field(..., description="Whether to call another tool after sending this message.")
    
class SendVoiceMessage(BaseToolArgs):
    """A tool to send a voice message to the user. You are able to speak using your voice this way."""
    tool_type: Literal["send_voice_message"]
    content: str = Field(..., description="Content of the voice message to send. Make it short and concise.")

class MemoryInsert(BaseToolArgs):
    """A tool to insert a memory into the vector database."""
    tool_type: Literal["memory_insert"]
    memory: str = Field(..., description="Detailed description of the memory to remember. Make it as detailed as possible.")
    
class MemoryRetrieve(BaseToolArgs):
    """A tool to retrieve a memory from the vector database."""
    tool_type: Literal["memory_retrieve"]
    memory: str = Field(..., description="Detailed description of the memory to retrieve.")
    
class DiceRoll(BaseToolArgs):
    """A tool to roll a dice."""
    tool_type: Literal["dice_roll"]
    sides: int = Field(..., description="Number of sides on the dice to roll.")

ToolArgs = Union[
    SendMessage,
    SendVoiceMessage,
    MemoryInsert,
    MemoryRetrieve,
    DiceRoll
]

class ReasoningModel(BaseModel):
    reasoning: str = Field(
        ...,
        description="Detailed and long step-by-step reasoning. Do not include the output here."
    )
    tool_args: ToolArgs = Field(
        ...,
        description="For tool calls, choose the appropriate tool and provide the necessary arguments here."
    )

    @field_validator("tool_args")
    def validate_tool_args(cls, v):
        if v is not None and not isinstance(v, BaseToolArgs):
            raise ValueError("Tool arguments must be a valid tool type")
        return v