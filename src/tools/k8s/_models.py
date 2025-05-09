from pydantic import BaseModel, Field

from kagent.config import get_model_client_config
from ._resource_types import ResourceTypes


class GenerateResourceToolConfig(BaseModel):
    model: str = Field(default="", description="The model to use for generating the resource. If empty, the default model will be used.")
    openai_api_key: str = Field(
        default="",
        description="API key for OpenAI services. If empty, the environment variable 'OPENAI_API_KEY' will be used.",
    )


class ApplyManifestInputs(BaseModel):
    """Inputs for the apply manifest command."""

    manifest: str = Field(..., description="The kubectl manifest YAML to apply.")
    namespace: str = Field(default="default", description="The namespace to apply the manifest to.")
    dry_run: bool = Field(default=False, description="Whether to run the apply command in dry-run mode.")


class BaseResourceInputs(BaseModel):
    """Base inputs for resource commands."""

    resource_type: ResourceTypes
    resource_name: str
    namespace: str = Field(default="default", description="The namespace to operate in.")
