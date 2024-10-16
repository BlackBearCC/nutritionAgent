from base.base_agent_module import BaseAgentModule
from frame import frame_prompt
import logging
import json

class FrameModule(BaseAgentModule):
    
    async def process(self, input_data: dict):
        analysis_result = input_data.get('analysis_result')
        user_info = input_data.get('user_info')
        specific_meal = input_data.get('specific_meal')
        weekly_meal_plan = input_data.get('weekly_meal_plan', [])
        
        if specific_meal:
            return await self.regenerate_specific_meal(analysis_result, user_info, specific_meal, weekly_meal_plan)
        
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
        
        logging.info("开始生成7天21餐食谱框架")
        
        # 第二步：使用批处理能力生成7天21餐食谱框架
        meal_plan_template = frame_prompt.meal_plan_prompt
        batch_inputs = []
        
        for day in range(1, 8):
            for meal in ['breakfast', 'lunch', 'dinner']:
                batch_inputs.append({
                    'batch_name': f"{day}_{meal}",
                    'prompt_template': meal_plan_template,
                    'invoke_input': {
                        "analysis_result": json.dumps(analysis_result),
                        "user_info": user_info,
                        "day_ingredients": json.dumps(ingredient_groups.get(str(day), [])),
                        "day": str(day),
                        "meal": meal
                    }
                })
        
        results = await self.batch_async_call_llm(batch_inputs)
        
        for batch_name, result in results.items():
            try:
                meal_plan = json.loads(result)
                weekly_meal_plan.append(meal_plan)
            except json.JSONDecodeError:
                logging.error(f"{batch_name} 的食谱框架不是有效的JSON格式")
        
        logging.info("成功生成7天21餐食谱框架")
        return weekly_meal_plan

    async def regenerate_specific_meal(self, analysis_result, user_info, specific_meal, weekly_meal_plan):
        day, meal = specific_meal['day'], specific_meal['meal']
        ingredients = self.get_ingredients_for_day(weekly_meal_plan, day)
        
        meal_plan_template = frame_prompt.meal_plan_prompt
        invoke_input = {
            "analysis_result": json.dumps(analysis_result),
            "user_info": user_info,
            "day_ingredients": json.dumps(ingredients),
            "day": day,
            "meal": meal
        }
        
        new_meal_plan = await self.async_call_llm(meal_plan_template, invoke_input)
        
        try:
            new_meal_plan = json.loads(new_meal_plan)
            for i, plan in enumerate(weekly_meal_plan):
                if plan['day'] == day and plan['meal'] == meal:
                    weekly_meal_plan[i] = new_meal_plan
                    break
            else:
                weekly_meal_plan.append(new_meal_plan)
            logging.info(f"成功重新生成第 {day} 天的 {meal}")
            return weekly_meal_plan
        except json.JSONDecodeError:
            logging.error(f"重新生成的第 {day} 天的 {meal} 不是有效的JSON格式")
            return weekly_meal_plan

    def get_food_database(self):
        # return ["鸡胸肉", "牛肉", "猪五花", "羊肉", "鸭肉", "鹅肉", "兔肉", "鱼肉", "虾", "蟹肉",
        #         "鱿鱼", "章鱼", "鸡翅", "鸡腿", "猪排", "牛排", "火腿", "培根", "香肠", "鸡肝",
        #         "猪肝", "牛舌", "猪蹄", "鸡爪", "鸭舌", "西兰花", "菠菜", "胡萝卜", "番茄", "黄瓜",
        #         "茄子", "豆腐", "鸡蛋", "牛奶", "酸奶", "燕麦", "全麦面包", "糙米", "红薯", "土豆"]
        return "无"

    def get_ingredients_for_day(self, weekly_meal_plan, day):
        all_ingredients = set()
        for plan in weekly_meal_plan:
            if plan['day'] == day:
                for dish in plan['menu']['dishes']:
                    all_ingredients.update(dish.get('ingredients', []))
        if not all_ingredients:
            logging.warning(f"第 {day} 天的食谱不存在或没有食材")
        return list(all_ingredients)
