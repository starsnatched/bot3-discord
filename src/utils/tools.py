import inspect
import sys
from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Type
from pydantic import Field

from utils.models import BaseToolArgs
from services.database import DatabaseService
import utils.models as models

@dataclass
class FormatConfig:
    indent_size: int = 4
    separator: str = "\n"
    section_separator: str = "\n\n"

class ToolFormatter:
    def __init__(self, config: FormatConfig = FormatConfig()):
        self.config = config
    
    def format_tool_type(self, tool_class: Type[BaseToolArgs]) -> str:
        return str(tool_class.__annotations__["tool_type"]).split("[")[-1].strip('"]')
    
    def format_field_type(self, field_type: Any) -> str:
        return (str(field_type)
            .replace("typing.", "")
            .replace("<class", "")
            .replace(">", "")
            .replace("'", "")
            .strip())
    
    def format_field(self, name: str, field: Field) -> str:
        if name == "tool_type":
            return ""
        field_type = self.format_field_type(field.annotation)
        field_desc = field.description or "No description available"
        indent = " " * self.config.indent_size
        return f"{indent}FIELD: {name}\n{indent}TYPE: {field_type}\n{indent}DESCRIPTION: {field_desc}"
    
    def format_tool(self, tool_class: Type[BaseToolArgs]) -> str:
        tool_type = self.format_tool_type(tool_class)
        description = dedent(tool_class.__doc__).strip() if tool_class.__doc__ else "No description available"
        
        fields = [
            self.format_field(name, field)
            for name, field in tool_class.model_fields.items()
        ]
        fields = [f for f in fields if f]
        
        sections = [
            f"TOOL_TYPE: {tool_type}",
            f"DESCRIPTION: {description}",
            "TOOL_ARGUMENTS"
        ]
        
        if fields:
            sections.extend(fields)
            
        return self.config.separator.join(sections)
    
async def get_tool_info(omit_disabled: bool = False) -> str:
    formatter = ToolFormatter()
    
    if omit_disabled:
        db = DatabaseService()
        disabled_tools = await db.get_disabled_tools()
        tools_set = {
            obj for name, obj in (
                inspect.getmembers(sys.modules[__name__]) + inspect.getmembers(models)
            )
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseToolArgs) and 
                obj != BaseToolArgs and 
                obj.model_fields.get('tool_type', None) and
                obj.model_fields['tool_type'].default not in disabled_tools)
        }
    else:
        tools_set = {
            obj for name, obj in (
                inspect.getmembers(sys.modules[__name__]) + inspect.getmembers(models)
            )
            if inspect.isclass(obj) and issubclass(obj, BaseToolArgs) and obj != BaseToolArgs
        }
    
    return formatter.config.section_separator.join(
        formatter.format_tool(tool) for tool in sorted(tools_set, key=lambda x: x.__name__)
    )