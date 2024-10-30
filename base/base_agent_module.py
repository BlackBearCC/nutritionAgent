from abc import ABC, abstractmethod
import os
from langchain_community.llms.tongyi import Tongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
import logging
import asyncio
from openai import RateLimitError
import json
import re
from typing import Dict, Any, Type

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
    
    async def async_call_llm(self, prompt_template, invoke_input: dict, llm_name="qwen-turbo", output_parser_type="str", max_retries=3, retry_delay=0.1, **kwargs):
        llm = Tongyi(model_name=llm_name, temperature=0.7, top_k=100, top_p=0.9, dashscope_api_key=self.llm_api_key)
        prompt_text = self.generate_prompt_text(prompt_template, **kwargs)
        prompt = PromptTemplate(template=prompt_text, input_variables=invoke_input.keys())
        
        # 根据参数选择输出解析器
        if output_parser_type == "json":
            output_parser = JsonOutputParser()
        else:
            output_parser = StrOutputParser()
        
        chain = prompt | llm | output_parser
        
        for attempt in range(max_retries):
            try:
                response = await chain.ainvoke(invoke_input)
                # response = response+"www" ##测试重试效果
                logging.info(f"Response: {response}")
                return response
            except RateLimitError:
                if attempt < max_retries - 1:
                    wait_time = min(retry_delay * (2 ** attempt), 0.5)  # 最大等待500ms
                    logging.warning(f"Rate limit reached, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    # 尝试使用备用LLM
                    llm = self._get_retry_llm(attempt)
                    chain = prompt | llm | output_parser
                    continue
                logging.error("Max retries reached for rate limit")
                raise
            except OutputParserException as e:
                if attempt < max_retries - 1:
                    wait_time = min(retry_delay * (2 ** attempt), 0.5)  # 最大等待500ms
                    logging.warning(f"Output parsing failed: {e}. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    # 解析错误时，尝试调整温度和模型
                    llm = self._get_retry_llm(attempt, error_type="parser")
                    chain = prompt | llm | output_parser
                    continue
                logging.error("Max retries reached for output parsing")
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = min(retry_delay * (2 ** attempt), 0.5)  # 最大等待500ms
                    logging.warning(f"Unexpected error: {e}. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    # 其他错误时，尝试切换API key和模型
                    llm = self._get_retry_llm(attempt, error_type="general")
                    chain = prompt | llm | output_parser
                    continue
                logging.error(f"Max retries reached for error: {e}")
                raise

    def generate_prompt_text(self, prompt_template, **kwargs):
        for key, value in kwargs.items():
            prompt_template = prompt_template.replace(f'{{{key}}}', str(value))
        return prompt_template

    def _get_retry_llm(self, attempt: int, error_type: str = "rate_limit") -> Tongyi:
        """根据重试次数和错误类型获取不同配置的LLM"""
        retry_configs = {
            "rate_limit": [
                {"model_name": "qwen-turbo", "temperature": 0.7, "api_key": os.getenv('DASHSCOPE_API_KEY_BACKUP')},  # 先换备用key
                {"model_name": "qwen-plus", "temperature": 0.7, "api_key": os.getenv('DASHSCOPE_API_KEY_BACKUP')},  # 换更强模型
                {"model_name": "qwen-turbo", "temperature": 0.7, "api_key": os.getenv('DASHSCOPE_API_KEY_BACKUP')}  # 最强模型
            ],
            "parser": [
                {"model_name": "qwen-turbo", "temperature": 0.5},  # 降低温度
                {"model_name": "qwen-plus", "temperature": 0.3},  # 更强模型+更低温度
                {"model_name": "qwen-turbo", "temperature": 0.7,"api_key": os.getenv('DASHSCOPE_API_KEY_BACKUP')}  # 最强模型+最低温度+切换key
            ],
            "general": [
                {"model_name": "qwen-turbo", "temperature": 0.7, "api_key": self.llm_api_key},
                {"model_name": "qwen-plus", "temperature": 0.5, "api_key": self.llm_api_key},
                {"model_name": "qwen-turbo", "temperature": 0.3, "api_key": os.getenv('DASHSCOPE_API_KEY_BACKUP')}
            ]
        }
        
        configs = retry_configs[error_type]
        config = configs[min(attempt, len(configs) - 1)]
        
        return Tongyi(
            model_name=config["model_name"],
            temperature=config.get("temperature", 0.7),
            top_k=100,
            top_p=0.9,
            dashscope_api_key=config.get("api_key", self.llm_api_key)
        )

    async def batch_async_call_llm(self, batch_inputs: list, output_parser_type="str"):
        tasks = []
        total_tasks = len(batch_inputs)
        
        for index, input_data in enumerate(batch_inputs, start=1):
            prompt_template = input_data.get('prompt_template')
            invoke_input = input_data.get('invoke_input', {})
            kwargs = input_data.get('kwargs', {})
            batch_name = input_data.get('batch_name', f'unnamed_batch_{index}')
            
            self.logger.info(f"创建任务: {batch_name} ({index}/{total_tasks})")
            task = asyncio.create_task(self._process_single_task(batch_name, prompt_template, invoke_input, kwargs, index, total_tasks, output_parser_type))
            tasks.append(task)

        self.logger.info(f"开始并发处理 {total_tasks} 个任务")
        results = await asyncio.gather(*tasks)
        self.logger.info(f"批处理完成，共处理 {total_tasks} 个任务")
        
        return dict(results)

    async def _process_single_task(self, batch_name, prompt_template, invoke_input, kwargs, index, total_tasks, output_parser_type):
        self.logger.info(f"处理中: {batch_name} ({index}/{total_tasks})")
        try:
            result = await self.async_call_llm(prompt_template, invoke_input, output_parser_type=output_parser_type, **kwargs)
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
