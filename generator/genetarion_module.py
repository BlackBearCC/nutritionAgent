from base.base_agent_module import BaseAgentModule
from generator.generation_prompt import generation_prompt

class GenerationModule(BaseAgentModule):
    
    async def process(self, analysis_result):
        prompt_template = generation_prompt.recipe_generation_template
        invoke_input = {
            "analysis_result": analysis_result,
        }
        
        try:
            result = await self.async_call_llm(prompt_template, invoke_input)
            
            # 这里可以添加一些后处理逻辑
            # 比如格式化食谱、检查是否包含所有必要的信息等
            
            return result
        except Exception as e:
            print(f"哎呀，生成食谱时遇到了一点小麻烦呢：{e}")
            return None

    # 可以添加其他辅助方法
    async def refine_recipe(self, initial_recipe):
        # 用于优化或调整初始生成的食谱
        pass

    async def check_nutritional_balance(self, recipe):
        # 检查食谱的营养平衡
        pass
