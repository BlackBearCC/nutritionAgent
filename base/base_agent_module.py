from abc import ABC, abstractmethod
import os
from langchain_community.llms.tongyi import Tongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
import logging
import asyncio
from openai import RateLimitError
import json
import re

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
    
    async def async_call_llm(self, prompt_template, invoke_input: dict, llm_name="qwen-turbo", parse_json=False, **kwargs):
        llm = Tongyi(model_name=llm_name, temperature=0.7, top_k=100, top_p=0.9, dashscope_api_key=self.llm_api_key)
        prompt_text = self.generate_prompt_text(prompt_template, **kwargs)
        prompt = PromptTemplate(template=prompt_text, input_variables=invoke_input.keys())
        output_parser = StrOutputParser()
        chain = prompt | llm | output_parser
        try:
            response = await chain.ainvoke(invoke_input)
            logging.info(f"Response: {response}")
            if parse_json:
                return self.parse_json_response(response)
            return response
        except RateLimitError:
            logging.error("Rate limit reached, retrying...")
            response = await self.retry_chain(chain, kwargs)
            if parse_json:
                return self.parse_json_response(response)
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
    
    async def batch_async_call_llm(self, batch_inputs: list, parse_json=False):
        tasks = []
        total_tasks = len(batch_inputs)
        
        for index, input_data in enumerate(batch_inputs, start=1):
            prompt_template = input_data.get('prompt_template')
            invoke_input = input_data.get('invoke_input', {})
            kwargs = input_data.get('kwargs', {})
            batch_name = input_data.get('batch_name', f'unnamed_batch_{index}')
            
            self.logger.info(f"创建任务: {batch_name} ({index}/{total_tasks})")
            task = asyncio.create_task(self._process_single_task(batch_name, prompt_template, invoke_input, kwargs, index, total_tasks, parse_json))
            tasks.append(task)

        self.logger.info(f"开始并发处理 {total_tasks} 个任务")
        results = await asyncio.gather(*tasks)
        self.logger.info(f"批处理完成，共处理 {total_tasks} 个任务")
        
        return dict(results)

    async def _process_single_task(self, batch_name, prompt_template, invoke_input, kwargs, index, total_tasks, parse_json):
        self.logger.info(f"处理中: {batch_name} ({index}/{total_tasks})")
        try:
            result = await self.async_call_llm(prompt_template, invoke_input, parse_json=parse_json, **kwargs)
            self.logger.info(f"完成: {batch_name} ({index}/{total_tasks})")
            return batch_name, result
        except Exception as e:
            self.logger.error(f"批处理中出现错误 ({batch_name}): {e}")
            return batch_name, None

    def parse_json_response(self, response):
        self.logger.info("JSON解析优化")
        # 移除可能的 Markdown 代码块标记
        response = re.sub(r'```json\s*|\s*```', '', response.strip())
        
        # 尝试提取 JSON 部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试修复常见问题
            try:
                # 替换单引号为双引号
                response = response.replace("'", '"')
                # 确保键值对之间有逗号
                response = re.sub(r'}\s*{', '},{', response)
                # 移除尾部可能的逗号
                response = re.sub(r',\s*}', '}', response)
                # 确保整个字符串是一个有效的 JSON 对象
                if not response.startswith('{'):
                    response = '{' + response
                if not response.endswith('}'):
                    response = response + '}'
                return json.loads(response)
            except json.JSONDecodeError as e:
                self.logger.error(f"无法解析JSON响应: {str(e)}")
                return None
