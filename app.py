import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

# 导入所需的模块
from analyse.analysis_module import AnalysisModule
from frame import frame_prompt
from frame.frame_module import FrameModule
from evaluation.evaluation_module import EvaluationModule
# from utils.generate_user_info import parse_user_info_string

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI()

class MealPlanRequest(BaseModel):
    user_info: str

class Dish(BaseModel):
    name: str
    quantity: str
    introduction: str

class Menu(BaseModel):
    total_calories: str
    dishes: List[Dish]

class MealPlan(BaseModel):
    day: int
    meal: str
    menu: Menu

class MealPlanResponse(BaseModel):
    weekly_meal_plan: List[MealPlan]

@app.post("/generate_meal_plan", response_model=MealPlanResponse)
async def generate_meal_plan(request: MealPlanRequest):
    try:
        # 解析用户信息
        user_info = request.user_info
        
        # 初始化模块
        analysis_module = AnalysisModule()
        frame_module = FrameModule()
        evaluation_module = EvaluationModule()

        # 分析用户信息
        analysis_input = {'user_info': user_info}
        analysis_result = await analysis_module.process(analysis_input)

        # 生成食谱框架
        frame_input = {
            'analysis_result': analysis_result,
            'user_info': user_info
        }
        ingredient_input, ingredient_result, meal_plan_input, weekly_meal_plan = await frame_module.process(frame_input)

        # 评估和优化食谱
        evaluation_history = []
        iteration_count = 0
        max_iterations = 5

        while iteration_count < max_iterations:
            evaluation_input = {
                'analysis_result': analysis_result,
                'user_info': user_info,
                'weekly_meal_plan': weekly_meal_plan,
                'evaluation_history': evaluation_history
            }
            evaluation_result = await evaluation_module.process(evaluation_input)

            if evaluation_result is None:
                logging.error(f"第 {iteration_count + 1} 次评估失败，跳过本次迭代")
                iteration_count += 1
                continue

            evaluation_history.append(evaluation_result)

            if evaluation_result.get('evaluation_complete', False):
                break

            improvement_suggestions = evaluation_result.get('improvement_suggestions', [])
            if improvement_suggestions:
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

                regenerated_meals = await frame_module.batch_async_call_llm(batch_inputs, parse_json=True)

                for batch_name, new_meal_plan in regenerated_meals.items():
                    if new_meal_plan:
                        day, meal = batch_name.split('_')[1:]
                        for i, plan in enumerate(weekly_meal_plan):
                            if plan['day'] == int(day) and plan['meal'] == meal:
                                weekly_meal_plan[i] = new_meal_plan
                                break
                        else:
                            weekly_meal_plan.append(new_meal_plan)

            iteration_count += 1

        # 处理返回的数据，确保包含完整的食谱信息
        processed_meal_plan = []
        for meal in weekly_meal_plan:
            processed_dishes = []
            for dish in meal['menu']['dishes']:
                processed_dish = Dish(
                    name=dish['name'],
                    quantity=dish['quantity'],
                    introduction=dish['introduction']
                )
                processed_dishes.append(processed_dish)

            processed_menu = Menu(
                total_calories=meal['menu']['total_calories'],
                dishes=processed_dishes
            )

            processed_meal = MealPlan(
                day=meal['day'],
                meal=meal['meal'],
                menu=processed_menu
            )
            processed_meal_plan.append(processed_meal)

        # 返回处理后的膳食计划
        return MealPlanResponse(weekly_meal_plan=processed_meal_plan)

    except Exception as e:
        logging.error(f"生成膳食计划时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail="生成膳食计划时发生内部错误")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
