import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./interview_agent.db"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    gemini_api_key: str = ""

    planner_model: str = "gemini/gemini-2.5-flash"
    interviewer_model: str = "gemini/gemini-2.5-flash"
    evaluator_model: str = "gemini/gemini-2.5-flash"
    report_model: str = "gemini/gemini-2.5-flash"

    max_questions: int = 10
    use_real_llm: bool = False
    log_level: str = "INFO"

    # Ragas & LlamaIndex settings
    ragas_faithfulness_threshold: float = 0.75
    ragas_eval_enabled: bool = True
    llama_index_top_k: int = 3

    # LangSmith tracing settings
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "ai-interview-agent"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    def model_for_agent(self, agent_name: str) -> str:
        mapping = {
            "planner": self.planner_model,
            "interviewer": self.interviewer_model,
            "evaluator": self.evaluator_model,
            "report": self.report_model,
        }
        return mapping.get(agent_name, self.planner_model)


settings = Settings()

# Set Gemini API key for LiteLLM if provided
if settings.gemini_api_key:
    os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
elif settings.google_api_key:
    os.environ["GEMINI_API_KEY"] = settings.google_api_key


# Propagate settings to standard environment variables for LangGraph and LiteLLM auto-detection
if settings.langchain_tracing_v2:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGSMITH_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGSMITH_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint

