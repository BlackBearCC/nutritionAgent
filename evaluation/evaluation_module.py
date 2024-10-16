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
        
        if not evaluation_history:
            # 首次评估
            evaluation_input = {
                "analysis_result": json.dumps(analysis_result),
                "user_info": user_info,
                "weekly_meal_plan": json.dumps(weekly_meal_plan)
            }
            prompt = weekly_meal_evaluation_prompt
        else:
            # 后续评估
            evaluation_input = {
                "analysis_result": json.dumps(analysis_result),
                "user_info": user_info,
                "weekly_meal_plan": json.dumps(weekly_meal_plan),
                "evaluation_history": json.dumps(evaluation_history)
            }
            prompt = follow_up_evaluation_prompt
        
        evaluation_result = await self.async_call_llm(prompt, evaluation_input)
        
        try:
            evaluation = json.loads(evaluation_result)
            logging.info("成功完成食谱评估")
            return evaluation
        except json.JSONDecodeError:
            logging.error("生成的评估结果不是有效的JSON格式")
            return None