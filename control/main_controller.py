import asyncio
import sys
import os
import json
import csv
from datetime import datetime

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

def log_module_io(module_name, input_data, output_data, csv_file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def format_data(data):
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        elif isinstance(data, dict):
            return {k: format_data(v) for k, v in data.items() if k != 'prompt_template'}
        elif isinstance(data, list):
            return [format_data(item) for item in data]
        else:
            return data
    
    formatted_input = format_data(input_data)
    formatted_output = format_data(output_data)
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerow([timestamp, module_name, "输入", json.dumps(formatted_input, ensure_ascii=False)])
        writer.writerow([timestamp, module_name, "输出", json.dumps(formatted_output, ensure_ascii=False)])

async def main():
    csv_file = "module_io_log.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Module", "Type", "Data"])

    user_info = """
    根据用户标签（女性，35岁，身高160厘米，体重45千克，尿酸高），主诉（降尿酸，美白），"""
    
    logging.info("开始分析用户信息")
    analysis_module = AnalysisModule()
    analysis_input = {'user_info': user_info}
    analysis_result = await analysis_module.process(analysis_input)
    log_module_io("AnalysisModule", analysis_input, analysis_result, csv_file)
    logging.info("用户信息分析完成")

    #################################
    logging.info("开始生成食谱框架")
    frame_module = FrameModule()
    frame_input = {
        'analysis_result': analysis_result,
        'user_info': user_info
    }
    ingredient_input, ingredient_result, meal_plan_input, meal_plan_result = await frame_module.process(frame_input)
    log_module_io("FrameModule_IngredientGeneration", ingredient_input, ingredient_result, csv_file)
    log_module_io("FrameModule_MealPlanGeneration", meal_plan_input, meal_plan_result, csv_file)
    weekly_meal_plan = meal_plan_result
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
        evaluation_input = {
            'analysis_result': analysis_result,
            'user_info': user_info,
            'weekly_meal_plan': weekly_meal_plan,
            'evaluation_history': evaluation_history
        }
        evaluation_result = await evaluation_module.process(evaluation_input)
        log_module_io(f"EvaluationModule_Iteration_{iteration_count + 1}", evaluation_input, evaluation_result, csv_file)
        evaluation_history.append(evaluation_result)

        if evaluation_result.get('evaluation_complete', False):
            logging.info("评估��成，无需进一步修改")
            break

        improvement_suggestions = evaluation_result.get('improvement_suggestions', [])
        if improvement_suggestions:
            logging.info("开始批量重新生成食谱")
            batch_inputs = []
            for suggestion in improvement_suggestions:
                batch_inputs.append({
                    'batch_name': f"{suggestion['day']}_{suggestion['meal']}",
                    'invoke_input': {
                        'analysis_result': json.dumps(analysis_result),
                        'user_info': user_info,
                        'day_ingredients': json.dumps(frame_module.get_ingredients_for_day(weekly_meal_plan, suggestion['day'])),
                        'day': suggestion['day'],
                        'meal': suggestion['meal']
                    }
                })
            
            batch_results = await frame_module.batch_async_call_llm(batch_inputs)
            log_module_io(f"FrameModule_Regeneration_Iteration_{iteration_count + 1}", batch_inputs, batch_results, csv_file)
            
            for batch_name, result in batch_results.items():
                try:
                    new_meal_plan = json.loads(result)
                    logging.info(f"新生成的餐食计划: {new_meal_plan}")
                    day = new_meal_plan.get('day')
                    meal = new_meal_plan.get('meal')
                    
                    if not all([day, meal, new_meal_plan.get('menu')]):
                        logging.error(f"新生成的餐食计划格式不正确: {new_meal_plan}")
                        continue
                    
                    for i, plan in enumerate(weekly_meal_plan):
                        if plan['day'] == day and plan['meal'] == meal:
                            weekly_meal_plan[i] = new_meal_plan
                            break
                    else:
                        weekly_meal_plan.append(new_meal_plan)
                    logging.info(f"成功重新生成第 {day} 天的 {meal}")
                except json.JSONDecodeError:
                    logging.error(f"重新生成的 {batch_name} 不是有效的JSON格式")
                except Exception as e:
                    logging.error(f"处理 {batch_name} 时发生错误: {str(e)}")

        logging.info(f"当前的weekly_meal_plan: {json.dumps(weekly_meal_plan, ensure_ascii=False, indent=2)}")

        iteration_count += 1

    if iteration_count == max_iterations:
        logging.warning("达到最大迭代次数，评估过程终止")

    # print("最终分析结果:", json.dumps(analysis_result, ensure_ascii=False, indent=2))
    # print("最终食谱框架结果:", json.dumps(weekly_meal_plan, ensure_ascii=False, indent=2))
    # print("评估历史:", json.dumps(evaluation_history, ensure_ascii=False, indent=2))

# 运行异步主函数
asyncio.run(main())
