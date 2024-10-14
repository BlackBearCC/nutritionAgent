import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from analyse.analysis_module import AnalysisModule
load_dotenv()

async def main():
    user_info ="""
    根据用户标签（女性，35岁，身高160厘米，体重45千克，尿酸高），主诉（降尿酸，美白），"""
    analysis_module = AnalysisModule()
    analysis_result = await analysis_module.process(user_info)
    print(analysis_result)

    

# 运行异步主函数
asyncio.run(main())


