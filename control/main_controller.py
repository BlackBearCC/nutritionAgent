import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from analyse.analysis_module import AnalysisModule
from frame.frame_module import FrameModule
import logging
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def main():
    user_info ="""
    根据用户标签（女性，35岁，身高160厘米，体重45千克，尿酸高），主诉（降尿酸，美白），"""
    analysis_module = AnalysisModule()
    analysis_result = await analysis_module.process({'user_info': user_info})
    
    frame_module = FrameModule()
    frame_result = await frame_module.process({
        'analysis_result': analysis_result,
        'user_info': user_info
    })
    print("分析结果:", analysis_result)
    print("定制食谱框架结果:", frame_result)

    

# 运行异步主函数
asyncio.run(main())


