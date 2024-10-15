from base.base_agent_module import BaseAgentModule
from generator.generation_prompt import recipe_generation_template
import json
import logging

class GenerationModule(BaseAgentModule):
    
    async def process(self, frame_result):
        batch_inputs = []
        
        for day, meals in frame_result.items():
            for meal_type, meal_details in meals.items():
                batch_inputs.append({
                    'batch_name': f"{day}_{meal_type}",
                    'prompt_template': recipe_generation_template,
                    'invoke_input': {
                        "nutrition": json.dumps(meal_details["nutrition"]),
                        "ingredients": ", ".join(meal_details["ingredients"]),
                        "cooking_method": meal_details["cooking_method"],
                        "meal_type": meal_type,
                    }
                })
        
        logging.info(f"开始生成 {len(batch_inputs)} 个食谱")
        results = await self.batch_async_call_llm(batch_inputs)
        
        weekly_recipes = {}
        for batch_name, recipe_json in results.items():
            day, meal_type = batch_name.split('_')
            if day not in weekly_recipes:
                weekly_recipes[day] = {}
            weekly_recipes[day][meal_type] = json.loads(recipe_json)
        
        logging.info("7天食谱生成完成")
        return weekly_recipes