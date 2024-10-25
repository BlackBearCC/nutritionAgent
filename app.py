import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime, timedelta
import httpx
from fastapi.background import BackgroundTasks

from openai import OpenAI

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
    userId: str
    customizedDate: str
    CC: List[str]
    sex: str
    age: int
    height: str
    weight: str
    healthDescription: str
    mealHabit: str
    mealAvoid: List[str]
    mealAllergy: List[str]
    mealTaste: List[str]
    mealStaple: List[str]
    mealSpicy: str
    mealSoup: str

class FoodDetail(BaseModel):
    foodDetail: Optional[List[str]] = [] ##食材
    foodName: str
    foodCount: str
    foodDesc: str
    customizedId: Optional[int] = None

class Meal(BaseModel):
    mealTypeText: str
    totalEnergy: int
    foodDetailList: List[FoodDetail]

class DayMeal(BaseModel):
    day: int
    meals: List[Meal]

class MealPlanData(BaseModel):
    id: str
    foodDate: str
    meals: List[Meal]  # 直接使用 meals，不需要 record 和 DayMeal

class MealPlanResponse(BaseModel):
    code: int
    msg: str
    data: MealPlanData

class FoodReplaceRequest(BaseModel):
    id: str
    mealTypeText: str
    CC: List[str]
    sex: str
    age: int
    height: str
    weight: str
    healthDescription: str
    mealHabit: str
    mealAvoid: List[str]
    mealAllergy: List[str]
    mealTaste: List[str]
    mealStaple: List[str]
    mealSpicy: str
    mealSoup: str
    replaceFoodList: List[FoodDetail]
    remainFoodList: List[FoodDetail]

# 生成食谱用的模型
class GenerateMealPlanData(BaseModel):
    id: str
    foodDate: str
    record: List[DayMeal]  # 使用 record 和 DayMeal

class GenerateMealPlanResponse(BaseModel):
    code: int
    msg: str
    data: GenerateMealPlanData

# 替换食材用的模型
class ReplaceMealPlanData(BaseModel):
    id: str
    foodDate: str
    meals: List[Meal]  # 直接使用 meals

class ReplaceMealPlanResponse(BaseModel):
    code: int
    msg: str
    data: ReplaceMealPlanData

# 添加基础响应模型
class BasicResponse(BaseModel):
    code: int
    msg: str
    data:str
# 请求模型
class PdfAnalysisRequest(BaseModel):
    id: str
    pdfUrl: str

# 响应数据模型
class PdfAnalysisData(BaseModel):
    id: str
    pdfAnalysis: str

# 响应模型
class PdfAnalysisResponse(BaseModel):
    code: int
    msg: str
    data: PdfAnalysisData


# 添加异步处理任务的函数
async def process_and_submit_meal_plan(
    request: MealPlanRequest,
    submit_url: str
):
    try:
        # 构建用户信息字符串
        user_info = f"""
        用户信息：
        性别：{request.sex}，年龄：{request.age}岁，身高：{request.height}，体重：{request.weight}
        出生日期：{(datetime.now() - timedelta(days=request.age*365)).strftime('%Y年%m月%d日')}
        健康兴趣：{', '.join(request.CC)}
        健康描述：{request.healthDescription}
        饮食习惯：{request.mealHabit}
        饮食禁忌：{', '.join(request.mealAvoid) if request.mealAvoid else '无'}
        食物过敏：{', '.join(request.mealAllergy)}
        口味偏好：{', '.join(request.mealTaste)}
        主食偏好：{', '.join(request.mealStaple)}
        辣度偏好：{request.mealSpicy}
        喝汤习惯：{request.mealSoup}
        """
        
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

        # 按天组织数据
        meals_by_day = {}
        for meal in weekly_meal_plan:
            day = int(meal['day'])
            if day not in meals_by_day:
                meals_by_day[day] = []
            
            processed_dishes = []
            for dish in meal['menu']['dishes']:
                processed_dish = FoodDetail(
                    foodDetail=dish.get('detail', []),  # 获取食材列表
                    foodName=dish['name'],
                    foodCount=dish['quantity'],
                    foodDesc=dish['introduction']
                )
                processed_dishes.append(processed_dish)

            # 修改这部分热量处理逻辑
            try:
                total_calories = meal['menu']['total_calories']
                if isinstance(total_calories, str):
                    # 如果是字符串，尝试清理并转换
                    total_energy = int(total_calories.replace('Kcal', '').replace('kcal', '').strip())
                elif isinstance(total_calories, (int, float)):
                    # 如果已经是数字，直接使用
                    total_energy = int(total_calories)
                else:
                    # 其他情况使用默认值
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

        # 使用 GenerateMealPlanData
        meal_data = GenerateMealPlanData(
            id=str(request.userId),
            foodDate=request.customizedDate,
            record=daily_records
        )
        
        result_data = GenerateMealPlanResponse(
            code=0,
            msg="成功",
            data=meal_data
        )
        logging.info(f"数据准备提交: {result_data}")
        
        # 提交结果
        async with httpx.AsyncClient() as client:
            response = await client.post(submit_url, json=result_data.dict())
            response.raise_for_status()
            logging.info(f"成功提交结果到 {submit_url}")
            
    except Exception as e:
        logging.error(f"后台处理任务发生错误: {str(e)}")
        # 这里可以添加错误处理的逻辑，比如重试或通知

# 修改生成食谱接口
@app.post("/generate_meal_plan", response_model=BasicResponse)
async def generate_meal_plan(
    request: MealPlanRequest,
    background_tasks: BackgroundTasks
):
    # 立即返回成功响应
    background_tasks.add_task(
        process_and_submit_meal_plan,
        request,
        "http://172.16.10.148:9050/food/view/intellectual-proxy/receiveFoodCustomizedResult"
    )
    return BasicResponse(code=0, msg="成功",data="")

# 替换食材的后台处理函数
async def process_and_submit_replacement(
    request: FoodReplaceRequest,
    submit_url: str
):
    try:
        # 构建用户信息字符串
        user_info = f"""
        户信息：
        性别：{request.sex}，年龄：{request.age}岁，身高：{request.height}，体重：{request.weight}
        健康兴趣：{', '.join(request.CC)}
        健康描述：{request.healthDescription}
        饮食习惯：{request.mealHabit}
        饮食禁忌：{', '.join(request.mealAvoid) if request.mealAvoid else '无'}
        食物过敏：{', '.join(request.mealAllergy)}
        口味偏好：{', '.join(request.mealTaste)}
        主食偏好：{', '.join(request.mealStaple)}
        辣度偏好：{request.mealSpicy}
        喝汤习惯：{request.mealSoup}
        """
        
        frame_module = FrameModule()
        
        # 构建替换食物的输入
        replace_input = {
            'id': request.id,
            'mealTypeText': request.mealTypeText,
            'user_info': user_info,  # 添加用户信息
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
        result = await frame_module.replace_foods(replace_input)
        
        if result['code'] != 0:
            raise HTTPException(status_code=400, detail=result['msg'])
            
        # 使用 ReplaceMealPlanData
        meal_data = ReplaceMealPlanData(
            id=request.id,
            foodDate=datetime.now().strftime("%Y-%m-%d"),
            meals=[  # 直接使用 meals
                Meal(
                    mealTypeText=request.mealTypeText,
                    totalEnergy=result['data']['meals'][0]['totalEnergy'],
                    foodDetailList=[
                        FoodDetail(
                            customizedId=food.get('customizedId'),
                            foodName=food['foodName'],
                            foodCount=food['foodCount'],
                            foodDesc=food['foodDesc']
                        ) for food in result['data']['meals'][0]['foodDetailList']
                    ]
                )
            ]
        )
        
        result_data = ReplaceMealPlanResponse(
            code=0,
            msg="成功",
            data=meal_data
        )
        logging.info(f"数据准备提交: {result_data}")
        # 提交结果
        async with httpx.AsyncClient() as client:
            response = await client.post(submit_url, json=result_data.dict())
            response.raise_for_status()
            logging.info(f"成功提交换结果到 {submit_url}")
            
    except Exception as e:
        logging.error(f"后台处理替换任务发生错误: {str(e)}")

# 修改替换食材接口
@app.post("/replace_foods", response_model=BasicResponse)
async def replace_foods(
    request: FoodReplaceRequest,
    background_tasks: BackgroundTasks
):
    # 立即返回成功响应
    background_tasks.add_task(
        process_and_submit_replacement,
        request,
        "http://172.16.10.148:9050/food/view/intellectual-proxy/receiveFoodCustomizedReplace"
    )
    return BasicResponse(code=0, msg="成功",data="")

# PDF分析的后台处理函数
async def process_and_submit_pdf_analysis(request: PdfAnalysisRequest):
    try:
        # 初始化 Moonshot 客户端
        client = OpenAI(
            api_key="sk-UNC90F5elMVhBc89xlhWCWPsKpicRwhh986pYJfH4jXK6Ba6",
            base_url="https://api.moonshot.cn/v1",
        )
        
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的健康报告分析助手。请生成此体检报告的健康问题总结，字数在150字以内，
                            ##要求##
                            1.不要提及人名
                            2.语言简明扼要，直接总结结论
                            3.仅输出异常项，正常项不需要输出
                            4.不输出多余解释和说明。
                            5.如果没有异常问题，直接输出"体检报告无异常"
                            6.不要遗漏健康问题和异常项

                            ##输出示例##
                            示例一：体检报告无异常。
                            示例二：存在电轴右偏、左侧小脑后下动脉血流速度增快、颈椎生理曲度变直、右肺微小结节等问题。""",
            },
            {
                "role": "system",
                "content": request.pdfUrl,
            },
            {
                "role": "user", 
                "content": "请仔细分析报告，100-150字"
            },
        ]
        
        # 使用 asyncio.to_thread 将同步操作转换为异步
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model="moonshot-v1-32k",
            messages=messages,
            temperature=0.7,
        )
        
        analysis_result = completion.choices[0].message.content
        
        result_data = {
            "code": 0,
            "msg": "成功",
            "data": {
                "id": request.id,
                "pdfAnalysis": analysis_result
            }
        }
        logging.info(f"数据准备提交: {result_data}")
        # 异步提交结果
        async with httpx.AsyncClient() as client:
            submit_url = "http://172.16.10.148:9050/food/view/intellectual-proxy/receivePdfResult"
            response = await client.post(submit_url, json=result_data)
            response.raise_for_status()
            logging.info(f"成功提交PDF分析结果到 {submit_url}")
            
    except Exception as e:
        logging.error(f"后台处理PDF分析任务发生错误: {str(e)}")

# 修改PDF分析接口
@app.post("/analyze_pdf", response_model=BasicResponse)
async def analyze_pdf(
    request: PdfAnalysisRequest,
    background_tasks: BackgroundTasks
):

    background_tasks.add_task(
        process_and_submit_pdf_analysis,
        request
    )
    return BasicResponse(code=0, msg="成功", data="")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

