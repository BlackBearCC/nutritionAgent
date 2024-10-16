import asyncio
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from analyse.analysis_module import AnalysisModule
from frame.frame_module import FrameModule
from generator.generation_module import GenerationModule
from evaluation.evaluation_module import EvaluationModule
from frame import frame_prompt
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
    weekly_meal_plan = await frame_module.process({
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


    evaluation_module = EvaluationModule()
    evaluation_history = []
    iteration_count = 0
    max_iterations = 5  

    while iteration_count < max_iterations:
        logging.info(f"开始第 {iteration_count + 1} 次评估")
        evaluation_result = await evaluation_module.process({
            'analysis_result': analysis_result,
            'user_info': user_info,
            'weekly_meal_plan': weekly_meal_plan,
            'evaluation_history': evaluation_history
        })
        evaluation_history.append(evaluation_result)

        if evaluation_result.get('evaluation_complete', False):
            logging.info("评估完成，无需进一步修改")
            break

        improvement_suggestions = evaluation_result.get('improvement_suggestions', [])
        if improvement_suggestions:
            logging.info("开始批量重新生成食谱")
            batch_inputs = []
            for suggestion in improvement_suggestions:
                batch_inputs.append({
                    'batch_name': f"{suggestion['day']}_{suggestion['meal']}",
                    'prompt_template': frame_prompt.daily_meal_plan_prompt,
                    'invoke_input': {
                        'analysis_result': json.dumps(analysis_result),
                        'user_info': user_info,
                        'day_ingredients': json.dumps(frame_module.get_ingredients_for_day(weekly_meal_plan, suggestion['day'])),
                        'day': suggestion['day']
                    }
                })
            
            batch_results = await frame_module.batch_async_call_llm(batch_inputs)
            
            for batch_name, result in batch_results.items():
                day, meal = batch_name.split('_')
                try:
                    new_meal_plan = json.loads(result)
                    weekly_meal_plan[day][meal] = new_meal_plan[meal]
                    logging.info(f"成功重新生成 {day} 的 {meal}")
                except json.JSONDecodeError:
                    logging.error(f"重新生成的 {day} 的 {meal} 不是有效的JSON格式")


        iteration_count += 1
 
    if iteration_count == max_iterations:
        logging.warning("达到最大迭代次数，评估过程终止")

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
