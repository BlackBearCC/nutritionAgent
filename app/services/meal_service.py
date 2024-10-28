import logging
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from app.core.config import Settings
from app.models.meal_plan import (
    MealPlanRequest, GenerateMealPlanResponse, 
    GenerateMealPlanData, DayMeal, Meal, FoodDetail
)
from analyse.analysis_module import AnalysisModule
from frame import frame_prompt
from frame.frame_module import FrameModule
from evaluation.evaluation_module import EvaluationModule

class MealPlanService:
    def __init__(self):
        self.settings = Settings()
        self.analysis_module = AnalysisModule()
        self.frame_module = FrameModule()
        self.evaluation_module = EvaluationModule()

    def _build_user_info(self, request: MealPlanRequest) -> str:
        return f"""
        用户信息：
        性别：{request.sex if request.sex else '未知'}
        年龄：{f'{request.age}岁' if request.age else '未知'}
        身高：{request.height if request.height else '未知'}
        体重：{request.weight if request.weight else '未知'}
        出生日期：{(datetime.now() - timedelta(days=request.age*365)).strftime('%Y年%m月%d日') if request.age else '未知'}
        健康兴趣：{', '.join(request.CC) if request.CC else '无'}
        健康描述：{request.healthDescription if request.healthDescription else '无'}
        饮食习惯：{request.mealHabit if request.mealHabit else '无'}
        饮食禁忌：{', '.join(request.mealAvoid) if request.mealAvoid else '无'}
        食物过敏：{', '.join(request.mealAllergy) if request.mealAllergy else '无'}
        口味偏好：{', '.join(request.mealTaste) if request.mealTaste else '无'}
        主食偏好：{', '.join(request.mealStaple) if request.mealStaple else '无'}
        辣度偏好：{request.mealSpicy if request.mealSpicy else '无'}
        喝汤习惯：{request.mealSoup if request.mealSoup else '无'}
        """

    async def generate_meal_plan(self, request: MealPlanRequest):
        try:
            user_info = self._build_user_info(request)
            
            # 分析用户信息
            analysis_result = await self.analysis_module.process({'user_info': user_info})

            # 生成食谱框架
            frame_input = {
                'analysis_result': analysis_result,
                'user_info': user_info
            }
            ingredient_input, ingredient_result, meal_plan_input, weekly_meal_plan = await self.frame_module.process(frame_input)

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
                evaluation_result = await self.evaluation_module.process(evaluation_input)

                if evaluation_result is None:
                    logging.error(f"第 {iteration_count + 1} 次评估失败，跳过本次迭代")
                    iteration_count += 1
                    continue

                evaluation_history.append(evaluation_result)

                if evaluation_result.get('evaluation_complete', False):
                    break

                # 获取改进建议
                improvement_suggestions = evaluation_result.get('improvement_suggestions', [])
                if improvement_suggestions:
                    # 批量处理改进建议
                    batch_inputs = [
                        {
                            'batch_name': f"meal_{suggestion['day']}_{suggestion['meal']}",
                            'prompt_template': frame_prompt.regenerate_meal_plan_prompt,
                            'invoke_input': {
                                "analysis_result": analysis_result,
                                "user_info": user_info,
                                "day": suggestion['day'],
                                "meal": suggestion['meal'],
                                "previous_meal": json.dumps(next(
                                    (plan for plan in weekly_meal_plan 
                                     if plan['day'] == int(suggestion['day']) 
                                     and plan['meal'] == suggestion['meal']), 
                                    None
                                )),
                                "improvement_suggestion": suggestion['suggestion']
                            }
                        }
                        for suggestion in improvement_suggestions
                    ]

                    # 批量调用LLM生成新的膳食计划
                    regenerated_meals = await self.frame_module.batch_async_call_llm(
                        batch_inputs, 
                        parse_json=True
                    )

                    # 更新膳食计划
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
                logging.info(f"完成第 {iteration_count} 次迭代")

            # 按天组织数据
            meals_by_day = {}
            for meal in weekly_meal_plan:
                day = int(meal['day'])
                if day not in meals_by_day:
                    meals_by_day[day] = []
                
                processed_dishes = []
                for dish in meal['menu']['dishes']:
                    processed_dish = FoodDetail(
                        foodDetail=dish.get('detail', []),
                        foodName=dish['name'],
                        foodCount=dish['quantity'],
                        foodDesc=dish['introduction']
                    )
                    processed_dishes.append(processed_dish)

                # 处理热量值
                try:
                    total_calories = meal['menu']['total_calories']
                    if isinstance(total_calories, str):
                        total_energy = int(total_calories.replace('Kcal', '').replace('kcal', '').strip())
                    elif isinstance(total_calories, (int, float)):
                        total_energy = int(total_calories)
                    else:
                        total_energy = 0
                        logging.warning(f"无法识别的热量格式: {total_calories}，使用默认值 {total_energy}")
                except (ValueError, AttributeError) as e:
                    total_energy = 0
                    logging.warning(f"处理热量值时出错: {str(e)}，使用默认值 {total_energy}")

                processed_meal = Meal(
                    mealTypeText=meal['meal'],
                    totalEnergy=total_energy,
                    foodDetailList=processed_dishes
                )
                meals_by_day[day].append(processed_meal)

            # 构建每天的记录
            daily_records = []
            for day, meals in meals_by_day.items():
                daily_record = DayMeal(
                    day=day,
                    meals=meals
                )
                daily_records.append(daily_record)

            # 构建最终响应
            meal_data = GenerateMealPlanData(
                userId=str(request.userId),
                foodDate=request.customizedDate,
                record=daily_records
            )
            
            result = GenerateMealPlanResponse(
                code=0,
                msg="成功",
                data=meal_data
            )

            return result

        except Exception as e:
            logging.error(f"生成膳食计划时发生错误: {str(e)}")
            raise

    async def submit_meal_plan(self, meal_plan: GenerateMealPlanResponse) -> None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.settings.MEAL_PLAN_SUBMIT_URL,
                    json=meal_plan.dict(),
                    timeout=30.0
                )
                response.raise_for_status()
                logging.info("成功提交膳食计划")
        except Exception as e:
            logging.error(f"提交膳食计划时发生错误: {str(e)}")
            raise