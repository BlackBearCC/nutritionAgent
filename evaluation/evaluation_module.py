from base.base_agent_module import BaseAgentModule
from evaluation.evaluation_prompt import weekly_meal_evaluation_prompt, follow_up_evaluation_prompt
import json
import logging

class EvaluationModule(BaseAgentModule):
    
    async def process(self, input_data: dict):
        analysis_result = input_data.get('analysis_result')
        user_info = input_data.get('user_info')
        weekly_meal_plan = input_data.get('weekly_meal_plan')
        evaluation_history = input_data.get('evaluation_history', [])
        
        logging.info("开始评估7天食谱")
        
        evaluation_input = {
            "analysis_result": analysis_result,
            "user_info": user_info,
            "weekly_meal_plan": weekly_meal_plan
        }
        
        if evaluation_history:
            evaluation_input["evaluation_history"] = evaluation_history
            prompt = follow_up_evaluation_prompt
        else:
            prompt = weekly_meal_evaluation_prompt
        # evaluation_result = await self.async_call_llm(prompt, evaluation_input,llm_name="qwen2-72b-instruct")
        evaluation_result = await self.async_call_llm(prompt, evaluation_input,llm_name="qwen-turbo")
        
        try:
            evaluation = json.loads(evaluation_result)
            logging.info("成功完成食谱评估")
            return evaluation
        except json.JSONDecodeError:
            logging.error("生成的评估结果不是有效的JSON格式")
            return None
