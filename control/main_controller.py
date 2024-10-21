import asyncio
import sys
import os
import json
import csv
from datetime import datetime
import time

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

from utils.csv_logger import CSVLogger, log_module_io

async def main():
    start_time = time.time()
    csv_logger = CSVLogger("module_io_log.csv")
    with open(csv_logger.file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Module", "Type", "Data"])

    user_info = """
    根据用户标签（女性，35岁，身高160厘米，体重45千克，尿酸高），主诉（降尿酸，美白），喜欢吃川菜"""
    
    logging.info("开始分析用户信息")
    analysis_module = AnalysisModule()
    analysis_start_time = time.time()
    analysis_input = {'user_info': user_info}
    analysis_result = await analysis_module.process(analysis_input)
    analysis_execution_time = time.time() - analysis_start_time
    log_module_io(csv_logger, "AnalysisModule", analysis_input, analysis_result, analysis_execution_time)
    logging.info("用户信息分析完成")

    #################################
    logging.info("开始生成食谱框架")
    frame_module = FrameModule()
    frame_start_time = time.time()
    frame_input = {
        'analysis_result': analysis_result,
        'user_info': user_info
    }
    ingredient_input, ingredient_result, meal_plan_input, weekly_meal_plan = await frame_module.process(frame_input)
    frame_execution_time = time.time() - frame_start_time
    log_module_io(csv_logger, "FrameModule_IngredientGeneration", ingredient_input, ingredient_result, frame_execution_time)
    log_module_io(csv_logger, "FrameModule_MealPlanGeneration", meal_plan_input, weekly_meal_plan, frame_execution_time)
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
    total_evaluation_time = 0
    total_regeneration_time = 0

    while iteration_count < max_iterations:
        logging.info(f"开始第 {iteration_count + 1} 次评估")
        evaluation_start_time = time.time()
        evaluation_input = {
            'analysis_result': analysis_result,
            'user_info': user_info,
            'weekly_meal_plan': weekly_meal_plan,
            'evaluation_history': evaluation_history
        }
        evaluation_result = await evaluation_module.process(evaluation_input)
        evaluation_execution_time = time.time() - evaluation_start_time
        total_evaluation_time += evaluation_execution_time
        log_module_io(csv_logger, f"EvaluationModule_Iteration_{iteration_count + 1}", evaluation_input, evaluation_result, evaluation_execution_time)
        evaluation_history.append(evaluation_result)

        if evaluation_result.get('evaluation_complete', False):
            logging.info("评估完成，无需进一步修改")
            break

        improvement_suggestions = evaluation_result.get('improvement_suggestions', [])
        if improvement_suggestions:
            logging.info("开始批量重新生成食谱")
            regeneration_start_time = time.time()
            
            # 准备批量处理的输入
            batch_inputs = [
                {
                    'batch_name': f"meal_{suggestion['day']}_{suggestion['meal']}",
                    'prompt_template': frame_prompt.regenerate_meal_plan_prompt,
                    'invoke_input': {
                        "analysis_result": analysis_result,
                        "user_info": user_info,
                        "day": suggestion['day'],
                        "meal": suggestion['meal'],
                        "previous_meal": json.dumps(next((plan for plan in weekly_meal_plan if plan['day'] == int(suggestion['day']) and plan['meal'] == suggestion['meal']), None)),
                        "improvement_suggestion": suggestion['suggestion']
                    }
                }
                for suggestion in improvement_suggestions
            ]

            # 批量重新生成食谱
            regenerated_meals = await frame_module.batch_async_call_llm(batch_inputs, parse_json=True)

            # 更新 weekly_meal_plan
            for batch_name, new_meal_plan in regenerated_meals.items():
                if new_meal_plan:
                    day, meal = batch_name.split('_')[1:]
                    for i, plan in enumerate(weekly_meal_plan):
                        if plan['day'] == int(day) and plan['meal'] == meal:
                            weekly_meal_plan[i] = new_meal_plan
                            break
                    else:
                        weekly_meal_plan.append(new_meal_plan)

            regeneration_execution_time = time.time() - regeneration_start_time
            total_regeneration_time += regeneration_execution_time
            log_module_io(csv_logger, f"FrameModule_Regeneration_Iteration_{iteration_count + 1}", improvement_suggestions, weekly_meal_plan, regeneration_execution_time)

        iteration_count += 1

    if iteration_count == max_iterations:
        logging.warning("达到最大迭代次数，评估过程终止")

    # 记录最终的完整7天膳食计划
    log_module_io(csv_logger, "FinalMealPlan", {}, weekly_meal_plan, 0)
    logging.info("最终的7天膳食计划已记录到module_io_log.csv")

    # 记录评估历史
    log_module_io(csv_logger, "EvaluationHistory", {}, evaluation_history, 0)
    logging.info("评估历史已记录到module_io_log.csv")

    # 最终摘要
    total_execution_time = time.time() - start_time
    summary = {
        "总迭代次数": iteration_count,
        "最终评分": evaluation_result.get('overall_score', 'N/A'),
        "最终评价": evaluation_result.get('general_comments', 'N/A'),
        "分析模块耗时": f"{analysis_execution_time:.2f}秒",
        "框架生成耗时": f"{frame_execution_time:.2f}秒",
        "评估总耗时": f"{total_evaluation_time:.2f}秒",
        "重新生成总耗时": f"{total_regeneration_time:.2f}秒",
        "总耗时": f"{total_execution_time:.2f}秒"
    }
    log_module_io(csv_logger, "FinalSummary", {}, summary, total_execution_time)

    logging.info("膳食计划生成和评估过程完成")
    logging.info(f"总迭代次数: {iteration_count}")
    logging.info(f"最终评分: {evaluation_result.get('overall_score', 'N/A')}")
    logging.info(f"最终评价: {evaluation_result.get('general_comments', 'N/A')}")
    logging.info(f"总耗时: {total_execution_time:.2f}秒")

# 运行异步主函数
asyncio.run(main())
