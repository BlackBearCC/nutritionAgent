from base.base_agent_module import BaseAgentModule
from analyse import analysis_prompt

class AnalysisModule(BaseAgentModule):
    
    async def process(self, user_input):

        # prompt_template = analysis_prompt.analysis_templet
        # 获取每日所需热量计算的提示模板
        calorie_calculation_templet = analysis_prompt.calorie_calculation_prompt
        # 获取宏量营养素比例的提示模板
        macronutrient_ratio_templet = analysis_prompt.macronutrient_ratio_prompt
        # 获取微量营养素需求的提示模板
        micronutrient_needs_templet = analysis_prompt.micronutrient_needs_prompt
        # 获取特定健康状况下的营养素调整建议的提示模板
        health_specific_nutrient_templet = analysis_prompt.health_specific_nutrient_prompt

        # invoke_input = {"input_text": user_input}
        
        batch_inputs = [
        {
            'batch_name': '每日所需热量',
            'prompt_template': calorie_calculation_templet,
            'invoke_input': {"input_text": user_input},
        },
        {
            'batch_name': '宏量营养素',
            'prompt_template': macronutrient_ratio_templet,
            'invoke_input': {"input_text": user_input},
        },
        {
            'batch_name': '微量营养素',
            'prompt_template': micronutrient_needs_templet,
            'invoke_input': {"input_text": user_input},
        },
        {
            'batch_name': '特殊健康营养素调整建议',
            'prompt_template': health_specific_nutrient_templet,
            'invoke_input': {"input_text": user_input},
        }
        ]

        # result = await self.async_call_llm(prompt_template, invoke_input)
        
        results = await self.batch_async_call_llm(batch_inputs)
        for batch_name, result in results.items():
            if result:
                print(f"{batch_name}: {result}")
            else:
                print(f"{batch_name}: 处理失败")
        return results

