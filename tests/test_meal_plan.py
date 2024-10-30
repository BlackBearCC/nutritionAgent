import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from datetime import datetime
import json
import time
from fastapi.testclient import TestClient
from app import app
from utils.generate_user_info import generate_user_info
from base.base_agent_module import BaseAgentModule

client = TestClient(app)

def format_meal_plan(response_data):
    """将响应数据转换为易读的格式"""
    try:
        result = []
        data = response_data.get('data', {})
        record = data.get('record', [])
        
        for day_record in record:
            day = day_record.get('day')
            meals = day_record.get('meals', [])
            
            for meal in meals:
                meal_type = meal.get('mealTypeText')
                total_energy = meal.get('totalEnergy')
                food_list = meal.get('foodDetailList', [])
                
                meal_str = f"\n第{day}天 {meal_type} (总热量: {total_energy}卡)\n"
                for food in food_list:
                    meal_str += f"- {food['foodName']} ({food['foodCount']})\n  {food['foodDesc']}\n"
                result.append(meal_str)
        
        return "\n".join(result)
    except Exception as e:
        return f"格式化失败: {str(e)}\n原始数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}"

class MealPlanEvaluator(BaseAgentModule):
    async def process(self, input_data: dict):
        """使用大模型评估膳食计划"""
        evaluation_prompt = """
        作为一位资深的营养学专家，请对以下膳食计划进行专业评估。

        用户信息：
        {user_info}

        膳食计划：
        {meal_plan}

        评估要求：
        1. 营养均衡性：评估主要营养素配比、微量元素是否充足
        2. 食材多样性：评估食材种类和搭配是否合理
        3. 用户需求匹配：根据用户健康标签和需求进行评估

        评分规则：
        - 基础分60分
        - 若违背用户健康禁忌项，直接判定60分
        - 根据营养均衡(40%)、食材多样(30%)、需求匹配(30%)计算最终得分

        请按以下格式输出：
        {{
            "score": <60-100的整数分数>,
            "evaluation": "<200字以内的评价，包含营养分析和对健康标签的影响>"
        }}
        """
        
        try:
            response = await self.async_call_llm(
                evaluation_prompt,
                {
                    "user_info": input_data["user_info"],
                    "meal_plan": input_data["meal_plan"]
                },
                output_parser_type="json",
                llm_name="qwen-max"
            )
            return response
        except Exception as e:
            self.logger.error(f"评估过程发生错误: {str(e)}")
            return {
                "score": 0,
                "evaluation": f"评估失败: {str(e)}"
            }

async def run_tests():
    # 检查是否存在已有的CSV文件
    csv_file = 'meal_plan_test_results.csv'
    if os.path.exists(csv_file):
        # 如果文件存在，读取现有数据
        results_df = pd.read_csv(csv_file, encoding='utf-8-sig')
        print(f"加载已有测试结果: {len(results_df)} 条记录")
    else:
        # 如果文件不存在，创建新的DataFrame
        results_df = pd.DataFrame(columns=[
            'timestamp', 
            'response_time_ms',
            'user_info', 
            'meal_plan', 
            'evaluation_score', 
            'evaluation_comments'
        ])
        print("创建新的测试结果文件")
    
    evaluator = MealPlanEvaluator()
    
    # 执行20次测试
    for i in range(50):
        print(f"执行第 {i+1} 次测试...")
        
        # 生成随机用户信息
        user_info = generate_user_info()
        
        # 构造请求数据
        request_data = {
            "userId": random.randint(1000, 9999),
            "customizedDate": datetime.now().strftime("%Y-%m-%d"),
            "CC": ["美白提亮", "淡化色斑"],
            "sex": "女" if "女" in user_info else "男",
            "age": int(user_info.split("年龄：")[1].split("岁")[0]),
            "height": user_info.split("身高：")[1].split("厘米")[0],
            "weight": user_info.split("体重：")[1].split("千克")[0],
            "healthDescription": "健康",
            "mealHabit": "正常三餐",
            "mealAvoid": [],
            "mealAllergy": user_info.split("食物过敏：")[1].split("\n")[0].split("，"),
            "mealTaste": user_info.split("口味偏好：")[1].split("\n")[0].split("，"),
            "mealStaple": user_info.split("主食偏好：")[1].split("\n")[0].split("，"),
            "mealSpicy": user_info.split("辣度偏好：")[1].split("\n")[0],
            "mealSoup": user_info.split("喝汤习惯：")[1].split("\n")[0]
        }
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 发送请求
            response = client.post("/generate_meal_plan", json=request_data)
            response_data = response.json()
            
            # 计算响应时间（毫秒）
            response_time = int((time.time() - start_time) * 1000)
            
            # 格式化膳食计划
            formatted_meal_plan = format_meal_plan(response_data)
            
            # 使用大模型评估结果
            evaluation = await evaluator.process({
                "user_info": user_info,
                "meal_plan": formatted_meal_plan
            })
            
            # 记录结果
            new_row = pd.DataFrame([{
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'response_time_ms': response_time,
                'user_info': user_info,
                'meal_plan': formatted_meal_plan,
                'evaluation_score': evaluation['score'],
                'evaluation_comments': evaluation['evaluation']
            }])
            
            # 追加新结果
            results_df = pd.concat([results_df, new_row], ignore_index=True)
            
            # 保存所有结果（包括之前的和新的）
            results_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"完成第 {i+1} 次测试，响应时间: {response_time}ms，总记录数: {len(results_df)}")
            
        except Exception as e:
            print(f"测试 {i+1} 发生错误: {str(e)}")
            continue
    
    print(f"测试完成，所有结果已保存到 {csv_file}，总记录数: {len(results_df)}")

if __name__ == "__main__":
    asyncio.run(run_tests())
