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
    @abstractmethod
    async def process(self, input_data):
        pass
    
    async def async_call_llm(self, prompt_template, invoke_input: dict, **kwargs):
        llm = Tongyi(model_name="qwen-turbo", temperature=0.7, top_k=100, top_p=0.9, dashscope_api_key=self.llm_api_key)
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
        for input_data in batch_inputs:
            prompt_template = input_data.get('prompt_template')
            invoke_input = input_data.get('invoke_input', {})
            kwargs = input_data.get('kwargs', {})
            batch_name = input_data.get('batch_name', 'unnamed_batch')  # 新增：获取批次名称
            task = asyncio.create_task(self.async_call_llm(prompt_template, invoke_input, **kwargs))
            tasks.append((batch_name, task))  # 将批次名称与任务一起存储
        
        results = {}
        for batch_name, task in tasks:
            try:
                result = await task
                results[batch_name] = result  # 使用批次名称作为键存储结果
            except Exception as e:
                logging.error(f"批处理中出现错误：{e}")
                results[batch_name] = None  # 错误时也使用批次名称存储 None
        
        return results
