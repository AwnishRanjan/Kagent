from typing import Any

from autogen_core import CancellationToken, Component
from autogen_core.tools import BaseTool, FunctionTool
from pydantic import BaseModel


def create_typed_fn_tool(fn_tool: FunctionTool, override_provider: str, class_name: str):
    """Creates a concrete typed fn tool class from a function tool."""

    class ToolConfig(BaseModel):
        pass

    class Tool(BaseTool, Component[ToolConfig]):
        component_provider_override = override_provider
        component_type = "tool"
        component_config_schema = ToolConfig
        component_description = fn_tool.description

        def __init__(self):
            self.fn_tool = fn_tool
            super().__init__(
                name=fn_tool.name,
                description=fn_tool.description,
                args_type=fn_tool.args_type(),
                return_type=fn_tool.return_type(),
            )

        async def run(self, args: ToolConfig, cancellation_token: CancellationToken) -> Any:
            return await self.fn_tool.run(args, cancellation_token)

        def _to_config(self) -> ToolConfig:
            return ToolConfig()

        @classmethod
        def _from_config(cls, config: ToolConfig):
            return cls()

    # Set the class name dynamically
    Tool.__name__ = class_name
    ToolConfig.__name__ = class_name + "Config"
    return (Tool, ToolConfig)
