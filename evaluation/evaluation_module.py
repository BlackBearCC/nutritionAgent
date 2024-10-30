from base.base_agent_module import BaseAgentModule
from evaluation.evaluation_prompt import weekly_meal_evaluation_prompt, follow_up_evaluation_prompt
from evaluation.default_evaluation import DefaultEvaluation
import json
import logging

class EvaluationModule(BaseAgentModule):
    
    async def process(self, input_data: dict):
        try:
            analysis_result = input_data.get('analysis_result')
            user_info = input_data.get('user_info')
            weekly_meal_plan = input_data.get('weekly_meal_plan')
            evaluation_history = input_data.get('evaluation_history', [])
            
            if not weekly_meal_plan:
                logging.error("食谱计划为空，返回默认评估")
                return DefaultEvaluation.get_default_evaluation(
                    is_follow_up=bool(evaluation_history)
                )
            
            logging.info("开始评估7天食谱")
            
            evaluation_input = {
                "analysis_result": analysis_result,
                "user_info": user_info,
                "weekly_meal_plan": weekly_meal_plan
            }
            
            is_follow_up = bool(evaluation_history)
            if is_follow_up:
                evaluation_input["evaluation_history"] = evaluation_history
                prompt = follow_up_evaluation_prompt
            else:
                prompt = weekly_meal_evaluation_prompt

            try:
                evaluation_result = await self.async_call_llm(
                    prompt, 
                    evaluation_input,
                    llm_name="qwen-turbo",
                    output_parser_type="json"
                )
                
                if not evaluation_result:
                    logging.warning("LLM返回空评估结果，使用默认评估")
                    return DefaultEvaluation.get_default_evaluation(
                        weekly_meal_plan,
                        is_follow_up
                    )
                
                # 验证评估结果的格式
                if not self._validate_evaluation_result(evaluation_result, is_follow_up):
                    logging.error("评估结果格式验证失败，使用默认评估")
                    return DefaultEvaluation.get_default_evaluation(
                        weekly_meal_plan,
                        is_follow_up
                    )
                
                logging.info("成功完成食谱评估")
                return evaluation_result
                
            except Exception as e:
                logging.error(f"调用LLM评估时发生错误: {str(e)}")
                return DefaultEvaluation.get_default_evaluation(
                    weekly_meal_plan,
                    is_follow_up
                )
                
        except Exception as e:
            logging.error(f"评估过程中发生错误: {str(e)}")
            return DefaultEvaluation.get_default_evaluation(
                is_follow_up=bool(evaluation_history)
            )

    def _validate_evaluation_result(self, result: dict, is_follow_up: bool) -> bool:
        """验证评估结果的格式是否正确"""
        try:
            # 检查基本字段
            required_fields = {"overall_score", "general_comments", "improvement_suggestions"}
            if is_follow_up:
                required_fields.add("evaluation_complete")
                
            if not all(field in result for field in required_fields):
                return False
                
            # 验证overall_score
            if not isinstance(result["overall_score"], int) or not 0 <= result["overall_score"] <= 100:
                return False
                
            # 验证improvement_suggestions
            if not isinstance(result["improvement_suggestions"], list):
                return False
                
            for suggestion in result["improvement_suggestions"]:
                if not all(key in suggestion for key in ["day", "meal", "issue", "suggestion"]):
                    return False
                if not isinstance(suggestion["day"], int) or not 1 <= suggestion["day"] <= 7:
                    return False
                if suggestion["meal"] not in ["早餐", "午餐", "晚餐"]:
                    return False
                    
            return True
            
        except Exception as e:
            logging.error(f"验证评估结果时发生错误: {str(e)}")
            return False
