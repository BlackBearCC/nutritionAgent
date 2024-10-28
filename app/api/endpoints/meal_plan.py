from fastapi import APIRouter, BackgroundTasks
from app.models.meal_plan import MealPlanRequest, BasicResponse
from app.services.meal_service import MealPlanService
import logging

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

    background_tasks.add_task(process_and_submit)
    return BasicResponse(code=0, msg="成功", data="")
