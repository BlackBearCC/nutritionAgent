from abc import ABC, abstractmethod
import os
from langchain_community.llms.tongyi import Tongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
import logging
import asyncio
from openai import RateLimitError

class BaseAgentModule(ABC):
    """
    定义基础Agent模块的类，提供基本的Agent功能和接口，用于继承和扩展。
    """
    def __init__(self):
        self.llm_api_key = os.getenv('DASHSCOPE_API_KEY')
        self.logger = logging.getLogger(self.__class__.__name__)
    @abstractmethod
    async def process(self, input_data: dict):
        pass
    
    async def async_call_llm(self, prompt_template, invoke_input: dict,llm_name="qwen-turbo", **kwargs):
        llm = Tongyi(model_name=llm_name, temperature=0.7, top_k=100, top_p=0.9, dashscope_api_key=self.llm_api_key)
        prompt_text = self.generate_prompt_text(prompt_template, **kwargs)
        prompt = PromptTemplate(template=prompt_text, input_variables=invoke_input.keys())
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser
        try:
            response = await chain.ainvoke(invoke_input)
            logging.info(f"Response: {response}")
            return response
        except RateLimitError:
            logging.error("Rate limit reached, retrying...")
            response = await self.retry_chain(chain, kwargs)
            return response
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            raise e
        
    ## 避免input之外占位符被替换，简易langchain特性处理    
    def generate_prompt_text(self, prompt_template, **kwargs):
        for key, value in kwargs.items():
            prompt_template = prompt_template.replace(f'{{{key}}}', str(value))
        return prompt_template

    async def retry_chain(self, chain, kwargs):
        try:
            response = await chain.ainvoke(kwargs)
            logging.info(f"Retry Response: {response}")
            return response
        except Exception as e:
            logging.error(f"Retry failed: {e}")
            raise e

    async def batch_async_call_llm(self, batch_inputs: list):
        tasks = []
        total_tasks = len(batch_inputs)
        
        for index, input_data in enumerate(batch_inputs, start=1):
            prompt_template = input_data.get('prompt_template')
            invoke_input = input_data.get('invoke_input', {})
            kwargs = input_data.get('kwargs', {})
            batch_name = input_data.get('batch_name', f'unnamed_batch_{index}')
            
            self.logger.info(f"创建任务: {batch_name} ({index}/{total_tasks})")
            task = asyncio.create_task(self._process_single_task(batch_name, prompt_template, invoke_input, kwargs, index, total_tasks))
            tasks.append(task)

        self.logger.info(f"开始并发处理 {total_tasks} 个任务")
        results = await asyncio.gather(*tasks)
        self.logger.info(f"批处理完成，共处理 {total_tasks} 个任务")
        
        return dict(results)

    async def _process_single_task(self, batch_name, prompt_template, invoke_input, kwargs, index, total_tasks):
        self.logger.info(f"处理中: {batch_name} ({index}/{total_tasks})")
        try:
            
            result = await self.async_call_llm(prompt_template, invoke_input, **kwargs)
            self.logger.info(f"完成: {batch_name} ({index}/{total_tasks})")
            return batch_name, result
        except Exception as e:
            self.logger.error(f"批处理中出现错误 ({batch_name}): {e}")
            return batch_name, None
