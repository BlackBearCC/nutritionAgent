import asyncio
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from analyse.analysis_module import AnalysisModule
from frame.frame_module import FrameModule
from generator.generation_module import GenerationModule
import logging
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def main():
    user_info = """
    根据用户标签（女性，35岁，身高160厘米，体重45千克，尿酸高），主诉（降尿酸，美白），"""
    
    logging.info("开始分析用户信息")
    analysis_module = AnalysisModule()
    analysis_result = await analysis_module.process({'user_info': user_info})
    logging.info("用户信息分析完成")

    #################################
    logging.info("开始生成食谱框架")
    frame_module = FrameModule()
    frame_result = await frame_module.process({
        'analysis_result': analysis_result,
        'user_info': user_info
    })
    logging.info("食谱框架生成完成")
    #################################


    #################################
    # 一次生成7天食谱耗时约35秒
    # logging.info("开始生成7天食谱")
    # generation_module = GenerationModule()
    # weekly_recipes = await generation_module.process({
    #     'analysis_result': analysis_result,
    #     'user_info': user_info
    # })
    # logging.info("7天食谱生成完成")
    #################################


    # print("分析结果:", json.dumps(analysis_result, ensure_ascii=False, indent=2))

    
    # logging.info("开始生成具体食谱")
    # generation_module = GenerationModule()
    # weekly_recipes = await generation_module.process(frame_result)
    # logging.info("具体食谱生成完成")
    
    # print("分析结果:", json.dumps(analysis_result, ensure_ascii=False, indent=2))
    # print("食谱框架结果:", json.dumps(frame_result, ensure_ascii=False, indent=2))
    # print("每周食谱:", json.dumps(weekly_recipes, ensure_ascii=False, indent=2))

# 运行异步主函数
asyncio.run(main())
