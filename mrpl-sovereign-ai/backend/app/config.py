"""
Central configuration. Loaded once, imported everywhere.

Deliberately has NO fields for any external/cloud API key:
this is a structural guarantee, not just a policy statement.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_env: str = "onprem"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Local LLM only — no cloud provider configuration is accepted here.
    local_llm_base_url: str = "http://127.0.0.1:11434/v1"
    local_llm_api_key: str = "not-needed-local"

    # Local model registry
    model_code: str = "qwen2.5-coder:32b"
    model_reasoning: str = "deepseek-r1:32b"
    model_general: str = "qwen2.5:32b-instruct"
    model_vision: str = "qwen2.5-vl:7b"
    model_small_fast: str = "phi4:14b"

    # Local workbench authentication
    admin_username: str = "admin"
    admin_password: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Local knowledge base / Chroma persistence
    chroma_persist_dir: str = "./data/chroma_store"

    # Code sandbox limits
    sandbox_timeout_seconds: int = 20
    sandbox_mem_limit_mb: int = 1024

    # Network sentinel
    net_monitor_interface: str = "auto"
    net_monitor_allowlist: str = "127.0.0.1,localhost,::1"

    # Local storage
    upload_dir: str = "./data/uploads"
    deliverable_dir: str = "./data/deliverables"
    db_path: str = "./data/workbench.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",

        # Do not fail if .env later contains a non-Settings value.
        # This prevents unrelated environment entries from blocking startup.
        extra="ignore",

        # Your legitimate model_code/model_reasoning/etc. settings use the
        # `model_` prefix. Restrict protected prefixes to `settings_`.
        protected_namespaces=("settings_",),
    )


settings = Settings()

for directory in (
        settings.chroma_persist_dir,
        settings.upload_dir,
        settings.deliverable_dir,
):
    Path(directory).mkdir(parents=True, exist_ok=True)