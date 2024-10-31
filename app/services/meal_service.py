import logging
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.core.config import get_settings
from app.models.meal_plan import (
    MealPlanRequest, GenerateMealPlanResponse, 
    GenerateMealPlanData, DayMeal, Meal, FoodDetail,
    FoodReplaceRequest, ReplaceMealPlanData, ReplaceMealPlanResponse
)
from analyse.analysis_module import AnalysisModule
from frame import frame_prompt
from frame.frame_module import FrameModule
from evaluation.evaluation_module import EvaluationModule

class MealPlanService:
    def __init__(self):
        self.settings = get_settings()  # 使用 get_settings() 而不是直接实例化
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
                        output_parser_type="json"
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

            # 确保生成7天21餐
            meals_by_day = {}
            for meal in weekly_meal_plan:
                day = int(meal['day'])
                if day not in meals_by_day:
                    meals_by_day[day] = []
                
                # 处理评估后的修改餐食
                if meal.get('is_regenerated'):  # 添加标记表示是否是重新生成的餐食
                    # 找到并替换原来的餐食
                    for i, existing_meal in enumerate(meals_by_day[day]):
                        if existing_meal.mealTypeText == meal['meal']:
                            meals_by_day[day][i] = self._process_meal(meal)
                            break
                else:
                    # 添加新的餐食
                    meals_by_day[day].append(self._process_meal(meal))
            
            # 验证每天都有3餐
            for day in range(1, 8):  # 7天
                if day not in meals_by_day:
                    meals_by_day[day] = []
                if len(meals_by_day[day]) != 3:
                    logging.warning(f"第{day}天的餐食数量不足3餐: {len(meals_by_day[day])}")
                
            # 构建最终响应
            daily_records = [
                DayMeal(day=day, meals=meals)
                for day, meals in sorted(meals_by_day.items())
            ]
            
            return GenerateMealPlanResponse(
                code=0,
                msg="成功",
                data=GenerateMealPlanData(
                    userId=str(request.userId),
                    foodDate=request.customizedDate,
                    record=daily_records
                )
            )
        
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

    def _process_meal(self, meal_data: dict) -> Meal:
        """处理单个餐食数据"""
        try:
            # 处理总热量，设置默认值为0
            total_calories = meal_data.get('menu', {}).get('total_calories', 180)
            total_energy = (
                int(total_calories.replace('Kcal', '').replace('kcal', '').strip())
                if isinstance(total_calories, str)
                else int(total_calories)
                if isinstance(total_calories, (int, float))
                else 0
            )
            
            processed_dishes = [
                FoodDetail(
                    foodDetail=dish.get('detail', []),
                    foodName=dish['name'],
                    foodCount=dish.get('quantity', '1份'),  # 默认份量
                    foodDesc=dish['introduction'],
                    foodEnergy = dish['energy'],
                    customizedId=dish.get('customizedId')
                )
                for dish in meal_data['menu']['dishes']
            ]
            
            return Meal(
                mealTypeText=meal_data['meal'],
                totalEnergy=total_energy,
                foodDetailList=processed_dishes
            )
        except Exception as e:
            logging.error(f"处理餐食数据时发生错误: {str(e)}")
            raise

    async def replace_foods(self, request: FoodReplaceRequest):
        """替换食材的服务方法"""
        try:
            # 构建用户信息
            user_info = self._build_user_info(request)
            
            # 构建替换食物的输入
            replace_input = {
                'id': request.id,
                'mealTypeText': request.mealTypeText,
                'user_info': user_info,
                'replaceFoodList': [
                    {
                        'foodName': food.foodName,
                        'foodCount': food.foodCount,
                        'foodDesc': food.foodDesc,
                        'customizedId': food.customizedId
                    } for food in request.replaceFoodList
                ],
                'remainFoodList': [
                    {
                        'foodName': food.foodName,
                        'foodCount': food.foodCount,
                        'foodDesc': food.foodDesc
                    } for food in request.remainFoodList
                ]
            }
            
            # 调用frame模块的替换功能
            result = await self.frame_module.replace_foods(replace_input)
            
            if result['code'] != 0:
                raise HTTPException(status_code=400, detail=result['msg'])

            # 构建响应数据
            meal_data = ReplaceMealPlanData(
                id=request.id,
                foodDate=datetime.now().strftime("%Y-%m-%d"),
                meals=[
                    Meal(
                        mealTypeText=request.mealTypeText,
                        totalEnergy=result['data']['meals'][0]['totalEnergy'],
                        foodDetailList=[
                            FoodDetail(
                                customizedId=food.get('customizedId'),
                                foodName=food['foodName'],
                                foodCount=food['foodCount'],
                                foodDesc=food['foodDesc'],
                                foodEnergy = food['foodEnergy'],
                                foodDetail=food.get('foodDetail', [])
                            ) for food in result['data']['meals'][0]['foodDetailList']
                        ]
                    )
                ]
            )
            
            return ReplaceMealPlanResponse(
                code=0,
                msg="成功",
                data=meal_data
            )

        except Exception as e:
            logging.error(f"替换食材时发生错误: {str(e)}")
            raise

    async def submit_replacement(self, replacement_plan: ReplaceMealPlanResponse) -> None:
        """提交替换结果的方法"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.settings.MEAL_PLAN_REPLACE_URL,
                    json=replacement_plan.dict(),
                    timeout=30.0
                )
                response.raise_for_status()
                logging.info("成功提交食材替换结果")
        except Exception as e:
            logging.error(f"提交食材替换结果时发生错误: {str(e)}")
            raise
