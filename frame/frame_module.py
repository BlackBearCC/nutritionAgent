from base.base_agent_module import BaseAgentModule
from frame import frame_prompt
import logging

class FrameModule(BaseAgentModule):
    
    async def process(self, input_data: dict):
        analysis_result = input_data.get('analysis_result')
        user_info = input_data.get('user_info')
        
        logging.info("开始 定制食谱框架")
        
        # 第一步：为三餐分配营养
        logging.info("步骤1：开始为三餐分配营养")
        nutrition_allocation_template = frame_prompt.nutrition_allocation_prompt
        nutrition_allocation_input = {
            "input_text": str(analysis_result),
        }
        nutrition_allocation_result = await self.async_call_llm(nutrition_allocation_template, nutrition_allocation_input, user_info=user_info)
        logging.info(f"步骤1完成")

        # 第二步：选择具体食材
        logging.info("步骤2：开始选择具体食材")
        food_selection_template = frame_prompt.food_selection_prompt
        food_selection_input = {
            "input_text": nutrition_allocation_result,
        }
        food_selection_result = await self.async_call_llm(food_selection_template, food_selection_input, 
                                                          user_info=user_info, 
                                                          food_database=str(self.get_food_database()))
        logging.info(f"步骤2完成")

        # 第三步：考虑具体烹饪方式
        logging.info("步骤3：开始考虑具体烹饪方式")
        cooking_method_template = frame_prompt.cooking_method_prompt
        cooking_method_input = {
            "input_text": nutrition_allocation_result,
        }
        cooking_method_result = await self.async_call_llm(cooking_method_template, cooking_method_input, 
                                                          food_selection=food_selection_result)
        logging.info(f"步骤3完成")

        # 合并结果
        final_result = {
            "nutrition_allocation": nutrition_allocation_result,
            "selected_ingredients": food_selection_result,
            "cooking_methods": cooking_method_result
        }

        logging.info("定制食谱框架 处理完成")
        return final_result

    def get_food_database(self):
        # 这里应该返回你的食材库，可能是从文件或数据库中读取
        # 为了示例，这里返回一个简单的列表
        return ["鸡胸肉", "西兰花", "燕麦", "鸡蛋", "三文鱼", "菠菜", "红薯", "豆腐", "牛肉", "猪五花", "羊肉", "鸭肉",
        "鹅肉", "兔肉", "鱼肉", "虾", "蟹肉",
        "鱿鱼", "章鱼", "鸡翅", "鸡腿", "猪排",
        "牛排", "火腿", "培根", "香肠", "鸡肝",
        "猪肝", "牛舌", "猪蹄", "鸡爪", "鸭舌"]
