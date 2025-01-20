import inspect
import sys
from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Type
from pydantic import Field

from utils.models import BaseToolArgs

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
        return f"{indent}FIELD: {name}\n{indent}TYPE: {field_type}\n{indent}DESCRIPTION: {field_desc}\n"
    
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
    
def get_tool_info() -> str:
    formatter = ToolFormatter()
    tools_set = {
        obj for name, obj in (
            inspect.getmembers(sys.modules[__name__], inspect.isclass)
        )
        if inspect.isclass(obj) and issubclass(obj, BaseToolArgs) and obj != BaseToolArgs
    }
    
    return formatter.config.section_separator.join(
        formatter.format_tool(tool) for tool in sorted(tools_set, key=lambda x: x.__name__)
    )

if __name__ == "__main__":
    print(get_tool_info())