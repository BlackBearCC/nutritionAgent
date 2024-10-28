from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API URLs
    PDF_ANALYSIS_SUBMIT_URL: str = "http://172.16.10.10:9050/food/view/intellectual-proxy/receivePdfResult"
    
    # Moonshot配置
    MOONSHOT_API_KEY: str = "sk-UNC90F5elMVhBc89xlhWCWPsKpicRwhh986pYJfH4jXK6Ba6"
    MOONSHOT_BASE_URL: str = "https://api.moonshot.cn/v1"
    
    # DashScope配置
    DASHSCOPE_API_KEY: Optional[str] = "sk-64554bb0973c4f09836c66fb43d508a2"
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = "sk-proj-tSELZo790pSLBMUG...kFJ00cd158DIMTNSTdZAuy6"
    
    # 日志配置
    LOG_PATH: Optional[str] = "app/app.log"
    
    class Config:
        env_file = ".env"
        extra = "allow"  # 允许额外的字段
