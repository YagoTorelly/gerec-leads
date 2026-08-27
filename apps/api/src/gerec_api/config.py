"""Configura\u00e7\u00e3o exclusiva do processo Python do backend."""

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Valores obrigat\u00f3rios fornecidos pelo ambiente do servidor."""

    mongodb_uri: str = Field(validation_alias="MONGODB_URI")
    mongodb_database: str = Field(validation_alias="MONGODB_DATABASE")
    app_secret: SecretStr = Field(validation_alias="APP_SECRET")

    model_config = SettingsConfigDict(extra="ignore")

    @classmethod
    def from_env(cls) -> "Settings":
        """Carrega a configura\u00e7\u00e3o sem inventar URI ou banco padr\u00e3o."""
        try:
            return cls()
        except ValidationError as error:
            missing = sorted(
                str(item["loc"][0])
                for item in error.errors()
                if item["type"] == "missing"
            )
            if missing:
                raise ValueError(
                    f"Missing required configuration: {', '.join(missing)}"
                ) from error
            raise
