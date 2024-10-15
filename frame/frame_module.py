from base.base_agent_module import BaseAgentModule
from frame import frame_prompt
import logging
import json

class FrameModule(BaseAgentModule):
    
    async def process(self, input_data: dict):
        analysis_result = input_data.get('analysis_result')
        user_info = input_data.get('user_info')
        
        logging.info("开始生成7天食谱框架")
        
        weekly_meal_plan_template = frame_prompt.weekly_meal_plan_prompt
        weekly_meal_plan_input = {
            "input_text": str(analysis_result)
        }
        weekly_meal_plan_result = await self.async_call_llm(
            weekly_meal_plan_template, 
            weekly_meal_plan_input,
            user_info=user_info,
            food_database=str(self.get_food_database())
        )
        
        try:
            weekly_meal_plan_json = json.loads(weekly_meal_plan_result)
            logging.info("成功生成7天食谱框架")
            return weekly_meal_plan_json
        except json.JSONDecodeError:
            logging.error("生成的7天食谱框架不是有效的JSON格式")
            return None

    def get_food_database(self):
        return ["鸡胸肉", "牛肉", "猪五花", "羊肉", "鸭肉", "鹅肉", "兔肉", "鱼肉", "虾", "蟹肉",
                "鱿鱼", "章鱼", "鸡翅", "鸡腿", "猪排", "牛排", "火腿", "培根", "香肠", "鸡肝",
                "猪肝", "牛舌", "猪蹄", "鸡爪", "鸭舌", "西兰花", "菠菜", "胡萝卜", "番茄", "黄瓜",
                "茄子", "豆腐", "鸡蛋", "牛奶", "酸奶", "燕麦", "全麦面包", "糙米", "红薯", "土豆"]
