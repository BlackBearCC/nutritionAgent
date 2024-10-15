from base.base_agent_module import BaseAgentModule
from generator.generation_prompt import weekly_recipe_generation_template
import json
import logging

class GenerationModule(BaseAgentModule):
    
    async def process(self, input_data: dict):
        analysis_result = input_data.get('analysis_result')
        user_info = input_data.get('user_info')
        
        logging.info("开始生成7天食谱")
        
        weekly_recipe_input = {
            "analysis_result": json.dumps(analysis_result),
            "user_info": user_info
        }
        
        weekly_recipe_result = await self.async_call_llm(weekly_recipe_generation_template, weekly_recipe_input,llm_name="qwen-max")
        
        try:
            weekly_recipes = json.loads(weekly_recipe_result)
            logging.info("成功生成7天食谱")
            return weekly_recipes
        except json.JSONDecodeError:
            logging.error("生成的7天食谱不是有效的JSON格式")
            return None