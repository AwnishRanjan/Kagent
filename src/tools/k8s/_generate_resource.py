import logging
from typing import Optional

from autogen_core import CancellationToken, Component
from autogen_core.tools import BaseTool
from pydantic import BaseModel, Field

from kagent.config import get_default_model_client, get_model_client_config
from ..common import LLMCallError, LLMTool, LLMToolConfig, LLMToolInput
from ._prompt_registry import get_system_prompt
from ._resource_types import ResourceTypes

logger = logging.getLogger(__name__)


class GenerateResourceToolConfig(LLMToolConfig):
    """Configuration for the GenerateResourceTool."""

    pass


class GenerateResourceToolInput(BaseModel):
    """Input for the GenerateResourceTool."""

    resource_description: str = Field(description="Detailed description of the resource to generate YAML for")
    resource_type: ResourceTypes = Field(description="Type of resource to generate")


class GenerateResourceError(LLMCallError):
    """Exception raised for errors in the resource generation process."""

    pass


class GenerateResourceTool(BaseTool, Component[GenerateResourceToolConfig]):
    """
    Tool for generating Kubernetes resource YAML.

    Args:
        config (GenerateResourceToolConfig): Tool configuration.
    """

    component_description = "Generate Kubernetes resource YAML based on a description"
    component_type = "tool"
    component_config_schema = GenerateResourceToolConfig
    component_provider_override = "kagent.tools.k8s.GenerateResourceTool"

    def __init__(self, config: Optional[GenerateResourceToolConfig] = None) -> None:
        if config is None:
            config = GenerateResourceToolConfig(model_client=get_model_client_config())

        self._llm_tool = LLMTool(config)

        super().__init__(
            args_type=GenerateResourceToolInput,
            return_type=str,
            name="generate_resource",
            description="Generate Kubernetes resource YAML based on a description",
        )

    async def run(self, args: GenerateResourceToolInput, cancellation_token: CancellationToken) -> str:
        """
        Generate Kubernetes resource YAML for the specified resource type.

        Args:
            args: The GenerateResourceToolInput containing the resource description and type.
            cancellation_token: Token to signal cancellation.

        Returns:
            The generated resource YAML as a string.
        """
        system_prompt = get_system_prompt(args.resource_type)
        user_message = args.resource_description

        if not system_prompt:
            return f"Error: No system prompt available for resource type: {args.resource_type}"

        try:
            llm_tool_input = LLMToolInput(system_prompt=system_prompt, user_message=user_message)
            return await self._llm_tool.run(llm_tool_input, cancellation_token)
        except Exception as e:
            logger.exception(f"Error generating resource YAML: {str(e)}")
            return f"Error generating resource YAML: {str(e)}"

    def _to_config(self) -> GenerateResourceToolConfig:
        # For now, just re-use the LLMTool's config
        return GenerateResourceToolConfig(model_client=self._llm_tool._model_client.dump_component())

    @classmethod
    def _from_config(cls, config: GenerateResourceToolConfig) -> "GenerateResourceTool":
        return cls(config)
