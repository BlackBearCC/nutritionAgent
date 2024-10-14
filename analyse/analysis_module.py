from base.base_agent_module import BaseAgentModule
from analyse import analysis_prompt

class AnalysisModule(BaseAgentModule):
    
    async def process(self, user_input):

        prompt_template = analysis_prompt.analysis_templet
        invoke_input = {"input_text": user_input}
        batch_inputs = [
        {
            'prompt_template': prompt_template,
            'invoke_input': {"input_text": user_input},
        },
        {
            'prompt_template': prompt_template,
            'invoke_input': {"input_text": user_input},
        },]

        # result = await self.async_call_llm(prompt_template, invoke_input)
        
        results = await self.batch_async_call_llm(batch_inputs)
        for result in results:
            if result:
                print(result)
            else:
                print("处理失败")
        return results

