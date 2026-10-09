from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://wqd:wqd_dev_pwd@localhost:5434/wqd"
    cors_origins: str = "http://localhost:3003"
    secret_key: str = "wqd-dev-secret-change-me"
    token_expire_days: int = 14
    # 种子管理员：首次启动 seed 时若该邮箱不存在则创建
    admin_email: str = "admin@wqd.local"
    admin_password: str = "wqd-admin-2026"

    # M3 RAG：生成模型走火山 ARK（agent plan 端点，OpenAI 兼容）
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/plan/v3"
    ark_api_key: str = ""
    ark_chat_model: str = "doubao-seed-2.0-lite"
    # 本地中文嵌入模型（ONNX，bge-small-zh，512 维，首次启动从镜像站拉取权重）
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_dim: int = 512
    hf_endpoint: str = "https://hf-mirror.com"
    # 检索参数
    retrieve_top_k: int = 6
    retrieve_min_score: float = 0.4  # cosine 相似度阈值，低于此视为“无可靠依据”
    ask_anonymous_daily: int = 10  # 未登录每日免费额度（按 client_id）
    ask_user_daily: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()
