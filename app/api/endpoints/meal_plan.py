from fastapi import APIRouter, BackgroundTasks
from app.models.meal_plan import MealPlanRequest, BasicResponse, GenerateMealPlanResponse, GenerateMealPlanData, DayMeal, FoodReplaceRequest
from app.services.meal_service import MealPlanService
from frame.default_meal_library import DefaultMealLibrary
import logging
from datetime import datetime

router = APIRouter()
meal_service = MealPlanService()

@router.post("/generate_meal_plan", response_model=BasicResponse)
async def generate_meal_plan(
    request: MealPlanRequest,
    background_tasks: BackgroundTasks
):
    async def process_and_submit():
        try:
            # 生成膳食计划
            meal_plan = await meal_service.generate_meal_plan(request)
            logging.info(f"准备提交数据：{meal_plan}")
            # 提交结果
            await meal_service.submit_meal_plan(meal_plan)
        except Exception as e:
            logging.error(f"处理膳食计划任务失败: {str(e)}")
            # 生成默认食谱
            try:
                default_plan = generate_default_meal_plan(request)
                logging.info("使用默认食谱作为备选方案")
                await meal_service.submit_meal_plan(default_plan)
            except Exception as submit_error:
                logging.error(f"提交默认食谱失败: {str(submit_error)}")

    background_tasks.add_task(process_and_submit)
    return BasicResponse(code=0, msg="成功", data="")

def generate_default_meal_plan(request: MealPlanRequest) -> GenerateMealPlanResponse:
    """生成默认的7天21餐食谱"""
    daily_records = []
    
    for day in range(1, 8):
        meals = []
        # 生成每天的三餐
        for meal_type in ['早餐', '午餐', '晚餐']:
            default_meal = DefaultMealLibrary.get_default_meal_plan(day, meal_type)
            processed_meal = meal_service._process_meal(default_meal)
            meals.append(processed_meal)
            
        daily_records.append(DayMeal(
            day=day,
            meals=meals
        ))
    
    return GenerateMealPlanResponse(
        code=0,
        msg="成功",
        data=GenerateMealPlanData(
            traceId=str(request.traceId),
            userId=str(request.userId),
            foodDate=request.customizedDate or datetime.now().strftime("%Y-%m-%d"),
            record=daily_records
        )
    )

@router.post("/replace_foods", response_model=BasicResponse)
async def replace_foods(
    request: FoodReplaceRequest,
    background_tasks: BackgroundTasks
):
    async def process_and_submit():
        try:
            # 生成替换方案
            replacement_plan = await meal_service.replace_foods(request)
            
            # 提交结果
            await meal_service.submit_replacement(replacement_plan)
        except Exception as e:
            logging.error(f"处理食材替换任务失败: {str(e)}")

    background_tasks.add_task(process_and_submit)
    return BasicResponse(code=0, msg="成功", data="")
