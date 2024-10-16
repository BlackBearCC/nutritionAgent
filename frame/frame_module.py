from base.base_agent_module import BaseAgentModule
from frame import frame_prompt
import logging
import json

class FrameModule(BaseAgentModule):
    
    async def process(self, input_data: dict):
        analysis_result = input_data.get('analysis_result')
        user_info = input_data.get('user_info')
        
        logging.info("开始生成食材和分组")
        
        # 第一步：生成食材并分组
        ingredient_generation_template = frame_prompt.ingredient_generation_prompt
        ingredient_input = {
            "analysis_result": json.dumps(analysis_result),
            "user_info": user_info,
            "food_database": self.get_food_database()
        }
        ingredient_result = await self.async_call_llm(ingredient_generation_template, ingredient_input)
        
        try:
            ingredient_groups = json.loads(ingredient_result)
            logging.info("成功生成食材分组")
        except json.JSONDecodeError:
            logging.error("生成的食材分组不是有效的JSON格式")
            return None
        
        logging.info("开始生成7天食谱框架")
        
        # 第二步：使用批处理能力生成7天食谱框架
        daily_meal_plan_template = frame_prompt.daily_meal_plan_prompt
        batch_inputs = []
        
        for day, ingredients in ingredient_groups.items():
            batch_inputs.append({
                'batch_name': day,
                'prompt_template': daily_meal_plan_template,
                'invoke_input': {
                    "analysis_result": json.dumps(analysis_result),
                    "user_info": user_info,
                    "day_ingredients": json.dumps(ingredients),
                    "day": day
                }
            })
        
        results = await self.batch_async_call_llm(batch_inputs)
        
        weekly_meal_plan = {}
        for day, result in results.items():
            try:
                daily_plan = json.loads(result)
                weekly_meal_plan[day] = daily_plan
            except json.JSONDecodeError:
                logging.error(f"{day} 的食谱框架不是有效的JSON格式")
        
        logging.info("成功生成7天食谱框架")
        return weekly_meal_plan

    def get_food_database(self):
        # return ["鸡胸肉", "牛肉", "猪五花", "羊肉", "鸭肉", "鹅肉", "兔肉", "鱼肉", "虾", "蟹肉",
        #         "鱿鱼", "章鱼", "鸡翅", "鸡腿", "猪排", "牛排", "火腿", "培根", "香肠", "鸡肝",
        #         "猪肝", "牛舌", "猪蹄", "鸡爪", "鸭舌", "西兰花", "菠菜", "胡萝卜", "番茄", "黄瓜",
        #         "茄子", "豆腐", "鸡蛋", "牛奶", "酸奶", "燕麦", "全麦面包", "糙米", "红薯", "土豆"]
        return "无"
