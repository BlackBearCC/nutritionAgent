from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API URLs
    PDF_ANALYSIS_SUBMIT_URL: str = "http://172.16.10.10:9050/food/view/intellectual-proxy/receivePdfResult"
    MEAL_PLAN_SUBMIT_URL: str = "http://172.16.10.10:9050/food/view/intellectual-proxy/receiveFoodCustomizedResult"
    MEAL_PLAN_REPLACE_URL: str = "http://172.16.10.10:9050/food/view/intellectual-proxy/receiveFoodCustomizedReplace"
    
    # Moonshot配置
    MOONSHOT_API_KEY: str = "sk-UNC90F5elMVhBc89xlhWCWPsKpicRwhh986pYJfH4jXK6Ba6"
    MOONSHOT_BASE_URL: str = "https://api.moonshot.cn/v1"
    
    # DashScope配置
    DASHSCOPE_API_KEY: str = "sk-64554bb0973c4f09836c66fb43d508a2"
    
    # OpenAI配置
    OPENAI_API_KEY: str = "sk-proj-tSELZo790pSLBMUG...kFJ00cd158DIMTNSTdZAuy6"
    
    # 日志配置
    LOG_PATH: str = "app/app.log"
    
    class Config:
        env_file = ".env"
        extra = "allow"  

@lru_cache()
def get_settings() -> Settings:
    """
    获取设置单例
    使用 lru_cache 确保只创建一次实例
    """
    return Settings()
