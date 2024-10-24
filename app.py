import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime, timedelta
import httpx
from fastapi.background import BackgroundTasks
import aiofiles
import os
from pathlib import Path
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
    mealTypeText: str
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

# 添加文件上传处理的响应模型
class HealthReportResponse(BaseModel):
    code: int
    msg: str
    data: str

# 添加文件上传和解析的后台处理函数
async def process_and_submit_health_report(
    file: UploadFile,
    submit_url: str
):
    try:
        # 创建临时文件夹用于存储上传的文件
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, file.filename)
        
        # 异步保存上传的文件
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        # 初始化 Moonshot 客户端
        client = OpenAI(
            api_key="sk-UNC90F5elMVhBc89xlhWCWPsKpicRwhh986pYJfH4jXK6Ba6",
            base_url="https://api.moonshot.cn/v1",
        )
        
        # 上传文件
        with open(file_path, 'rb') as f:
            file_object = client.files.create(
                file=Path(file_path), 
                purpose="file-extract"
            )
        
        # 获取文件内容
        file_content = client.files.content(file_id=file_object.id).text
        
        # 构建对话
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的健康报告分析助手。请分析这份健康体检报告，提取关键信息并给出健康建议。",
            },
            {
                "role": "system",
                "content": file_content,
            },
            {
                "role": "user", 
                "content": "请分析这份体检报告的主要问题和健康建议"
            },
        ]
        
        # 调用 chat-completion
        completion = client.chat.completions.create(
            model="moonshot-v1-32k",
            messages=messages,
            temperature=0.3,
        )
        
        # 获取分析结果
        analysis_result = completion.choices[0].message.content
        
        # 提交解析结果
        result_data = {
            'code': 0,
            'msg': '成功',
            'data': analysis_result
        }
        
        await client.post(submit_url, json=result_data)
        logging.info(f"成功提交健康报告解析结果到 {submit_url}")
        
        # 清理临时文件
        os.remove(file_path)
            
    except Exception as e:
        logging.error(f"处理健康报告时发生错误: {str(e)}")
        # 确保清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

# 修改健康报告解析接口
@app.post("/parse_health_report", response_model=HealthReportResponse)
async def parse_health_report(
    file: UploadFile = File(...)
):
    try:
        if not file.filename.endswith(('.pdf', '.doc', '.docx')):
            return HealthReportResponse(code=1, msg="仅支持 PDF 和 Word 文档格式", data="")
            
        # 创建临时文件夹用于存储上传的文件
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, file.filename)
        
        try:
            # 异步保存上传的文件
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            
            # 初始化 Moonshot 客户端
            client = OpenAI(
                api_key="sk-UNC90F5elMVhBc89xlhWCWPsKpicRwhh986pYJfH4jXK6Ba6",
                base_url="https://api.moonshot.cn/v1",
            )
            
            # 上传文件
            with open(file_path, 'rb') as f:
                file_object = client.files.create(
                    file=Path(file_path), 
                    purpose="file-extract"
                )
            
            # 获取文件内容
            file_content = client.files.content(file_id=file_object.id).text
            
            # 构建对话
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的健康报告分析助手。请分析这份健康体检报告，提取关键信息并给出健康建议。",
                },
                {
                    "role": "system",
                    "content": file_content,
                },
                {
                    "role": "user", 
                    "content": "请分析这份体检报告的主要问题和健康建议"
                },
            ]
            
            # 调用 chat-completion
            completion = client.chat.completions.create(
                model="moonshot-v1-32k",
                messages=messages,
                temperature=0.3,
            )
            
            # 获取分析结果
            analysis_result = completion.choices[0].message.content
            
            return HealthReportResponse(
                code=0,
                msg="成功",
                data=analysis_result
            )
                
        finally:
            # 确保清理临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
                
    except Exception as e:
        logging.error(f"处理健康报告时发生错误: {str(e)}")
        return HealthReportResponse(
            code=1, 
            msg=f"处理失败: {str(e)}", 
            data=""
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
