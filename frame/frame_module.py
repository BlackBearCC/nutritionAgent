from base.base_agent_module import BaseAgentModule
from frame import frame_prompt
import logging
import json
import datetime
from frame.default_meal_library import DefaultMealLibrary
import random


class FrameModule(BaseAgentModule):
    
    async def process(self, input_data: dict):
        try:
            analysis_result = input_data.get('analysis_result')
            user_info = input_data.get('user_info')
            specific_meal = input_data.get('specific_meal')
            weekly_meal_plan = input_data.get('weekly_meal_plan', [])
            
            if specific_meal:
                result = await self.regenerate_specific_meal(analysis_result, user_info, specific_meal, weekly_meal_plan)
                if not result:
                    day = int(specific_meal['day'])
                    meal = specific_meal['meal']
                    return self._get_default_meal_plan(day, meal)
                return result
            
            logging.info("开始生成食材和分组")
            
            # 第一步：为每日每餐生成食材并分组
            ingredient_input = {
                "analysis_result": analysis_result,
                "user_info": user_info,
                "food_database": self.get_food_database()
            }
            try:
                ingredient_result = await self.async_call_llm(
                    frame_prompt.ingredient_generation_prompt, 
                    ingredient_input, 
                    output_parser_type="json"
                )
                
                ingredient_result = json.loads(ingredient_result) if isinstance(ingredient_result, str) else ingredient_result
                recommended_ingredients = ingredient_result['recommended_ingredients']
                forbidden_ingredients = ingredient_result['forbidden_ingredients']
                logging.info("成功生成食材分组")
            except Exception as e:
                logging.error(f"生成食材分组失败: {str(e)}")
                ingredient_result = self._get_default_ingredients()
                recommended_ingredients = ingredient_result['recommended_ingredients']
                forbidden_ingredients = ingredient_result['forbidden_ingredients']
            
            logging.info("开始生成7天21餐食谱框架")
            
            # 第二步：使用批处理能力生成7天21餐食谱框架
            batch_inputs = []
            weekly_meal_plan = []
            
            for day in range(1, 8):
                for meal in ['早餐', '午餐', '晚餐']:
                    batch_inputs.append({
                        'batch_name': f"{day}_{meal}",
                        'prompt_template': frame_prompt.meal_plan_prompt,
                        'invoke_input': {
                            "analysis_result": analysis_result,
                            "user_info": user_info,
                            "meal_ingredients": {
                                "recommended": recommended_ingredients[str(day)][meal],
                                "forbidden": forbidden_ingredients
                            },
                            "day": str(day),
                            "meal": meal
                        }
                    })

            results = await self.batch_async_call_llm(batch_inputs, output_parser_type="json")
            
            # 处理每个餐次的结果，如果失败则使用默认值
            for day in range(1, 8):
                for meal in ['早餐', '午餐', '晚餐']:
                    batch_name = f"{day}_{meal}"
                    result = results.get(batch_name)
                    
                    try:
                        if result and isinstance(result, dict):
                            weekly_meal_plan.append(result)
                            logging.info(f"成功处理 {batch_name} 的结果")
                        else:
                            logging.warning(f"{batch_name} 生成失败，使用默认方案")
                            weekly_meal_plan.append(self._get_default_meal_plan(day, meal))
                    except Exception as e:
                        logging.error(f"处理 {batch_name} 时发生错误: {str(e)}")
                        weekly_meal_plan.append(self._get_default_meal_plan(day, meal))

            logging.info("完成7天21餐食谱框架生成")
            
            # 确保食谱完整性
            weekly_meal_plan = self._ensure_complete_meal_plan(weekly_meal_plan)
            
            # 移除 prompt_template，以便日志记录
            batch_inputs_for_log = [{k: v for k, v in input_data.items() if k != 'prompt_template'} for input_data in batch_inputs]
            
            return ingredient_input, ingredient_result, batch_inputs_for_log, weekly_meal_plan

        except Exception as e:
            logging.error(f"处理请求时发生错误: {str(e)}")
            # 生成完整的默认7天食谱
            ingredient_result = self._get_default_ingredients()
            weekly_meal_plan = []
            for day in range(1, 8):
                for meal in ['早餐', '午餐', '晚餐']:
                    weekly_meal_plan.append(self._get_default_meal_plan(day, meal))
            return ingredient_input, ingredient_result, None, weekly_meal_plan

    async def regenerate_specific_meal(self, analysis_result, user_info, specific_meal, weekly_meal_plan):
        day, meal = int(specific_meal['day']), specific_meal['meal']
        ingredients = self.get_ingredients_for_meal(weekly_meal_plan, day, meal)
        
        # 获取上次生成的结果
        previous_meal = next((plan for plan in weekly_meal_plan if plan['day'] == day and plan['meal'] == meal), None)
        
        # 获取改进建议
        improvement_suggestion = specific_meal.get('suggestion', '')
        
        try:
            prompt_input = {
                "analysis_result": analysis_result,
                "user_info": user_info,
                "meal_ingredients": ingredients,
                "day": str(day),
                "meal": meal,
                "previous_meal": previous_meal,
                "improvement_suggestion": improvement_suggestion
            }
            
            result = await self.async_call_llm(
                frame_prompt.meal_plan_prompt,
                prompt_input,
                output_parser_type="json"
            )
            
            if not result:
                logging.warning(f"重新生成第{day}天{meal}失败，使用默认方案")
                return self._get_default_meal_plan(day, meal)
                
            return result
            
        except Exception as e:
            logging.error(f"重新生成餐次时发生错误: {str(e)}")
            return self._get_default_meal_plan(day, meal)

    def get_food_database(self):
        return "无"

    def get_ingredients_for_meal(self, weekly_meal_plan, day, meal):
        day = int(day)
        meal_plan = next((plan for plan in weekly_meal_plan if plan['day'] == day and plan['meal'] == meal), None)
        if meal_plan:
            dishes = meal_plan['menu']['dishes']
            meal_ingredients = [dish['name'] for dish in dishes]
        else:
            meal_ingredients = []
        self.logger.info(f"获取第 {day} 天的 {meal} 食材")
        self.logger.info(f"第 {day} 天的 {meal} 食材: {meal_ingredients}")
        return meal_ingredients

    async def replace_foods(self, input_data: dict):
        """处理食物替换请求"""
        try:
            # 构建提示输入
            prompt_input = {
                "meal_type": input_data['mealTypeText'],
                "user_info": input_data.get('userInfo', ''),
                "replace_foods": input_data['replaceFoodList'],
                "remain_foods": input_data.get('remainFoodList', [])
            }
            
            llm_result = await self.async_call_llm(
                frame_prompt.replace_foods_prompt,
                prompt_input,
                llm_name="qwen2-72b-instruct",
                output_parser_type="json"
            )
            
            if not llm_result:
                # 使用默认库生成替换方案
                default_meal = self._get_default_meal_plan(1, input_data['mealTypeText'])
                default_dishes = default_meal['menu']['dishes']
                
                # 确保替换的数量与请求相匹配
                needed_count = len(input_data['replaceFoodList'])
                while len(default_dishes) < needed_count:
                    another_meal = self._get_default_meal_plan(2, input_data['mealTypeText'])
                    default_dishes.extend(another_meal['menu']['dishes'])
                
                food_details = []
                for i, replace_food in enumerate(input_data['replaceFoodList']):
                    if i < len(default_dishes):
                        food = default_dishes[i]
                        food_details.append({
                            "foodDetail": food.get('detail', []),
                            "foodName": food['name'],
                            "foodCount": food['quantity'],
                            "foodDesc": food['introduction'],
                            "foodEnergy": food['energy'],
                            "customizedId": replace_food.get('customizedId')
                        })
                
                total_energy = sum(food['foodEnergy'] for food in food_details)
                
                return {
                    "code": 0,
                    "msg": "成功(使用默认方案)",
                    "data": {
                        "id": input_data['id'],
                        "foodDate": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "meals": [{
                            "mealTypeText": input_data['mealTypeText'],
                            "totalEnergy": total_energy,
                            "foodDetailList": food_details
                        }]
                    }
                }
            
            # 确保llm_result是字典类型
            if isinstance(llm_result, str):
                llm_result = json.loads(llm_result)
            
            # 处理返回结果的结构
            food_details = []
            if 'food_details' in llm_result:
                food_details = llm_result['food_details']
            elif 'foodDetailList' in llm_result:
                food_details = llm_result['foodDetailList']
            else:
                raise ValueError("LLM返回结果缺少必要的食物详情字段")

            total_energy = llm_result.get('total_energy', 0)
            if 'totalEnergy' in llm_result:
                total_energy = llm_result['totalEnergy']
                
            # 确保返回的food_details中包含所有必要字段
            for food in food_details:
                if 'foodDetail' not in food:
                    food['foodDetail'] = []
                if 'customizedId' not in food:
                    # 如果LLM没有返回customizedId，尝试从原始请求中匹配
                    original_food = next(
                        (f for f in input_data['replaceFoodList'] if f['foodName'] == food['foodName']), 
                        None
                    )
                    if original_food:
                        food['customizedId'] = original_food.get('customizedId')
                        
            return {
                "code": 0,
                "msg": "成功",
                "data": {
                    "id": input_data['id'],
                    "foodDate": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "meals": [{
                        "mealTypeText": input_data['mealTypeText'],
                        "totalEnergy": total_energy,
                        "foodDetailList": [{
                            "foodDetail": food.get('foodDetail', []),
                            "foodName": food['foodName'],
                            "foodCount": food['foodCount'],
                            "foodDesc": food['foodDesc'],
                            "foodEnergy": food.get('foodEnergy', 0),
                            "customizedId": food.get('customizedId')
                        } for food in food_details]
                    }]
                }
            }
                
        except Exception as e:
            logging.error(f"替换食物时发生错误: {str(e)}")
            # 发生错误时也使用默认方案
            try:
                default_meal = self._get_default_meal_plan(1, input_data['mealTypeText'])
                # ... 与上面相同的默认方案处理逻辑 ...
            except Exception as e2:
                logging.error(f"使用默认方案也失败: {str(e2)}")
                return {
                    "code": 1,
                    "msg": f"替换食物失败: {str(e)}",
                    "data": {
                        "id": input_data.get('id', ''),
                        "foodDate": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "meals": []
                    }
                }

    def _get_default_meal_plan(self, day: int, meal: str) -> dict:
        return DefaultMealLibrary.get_default_meal_plan(day, meal)
        
    def _get_default_ingredients(self) -> dict:
        return DefaultMealLibrary.get_default_ingredients()

    def _validate_weekly_meal_plan(self, weekly_meal_plan: list) -> bool:
        """验证7天21餐的完整性"""
        try:
            if not weekly_meal_plan or len(weekly_meal_plan) != 21:
                return False
                
            # 用于检查每天每餐是否都存在
            meal_check = {
                day: {meal: False for meal in ['早餐', '午餐', '晚餐']}
                for day in range(1, 8)
            }
            
            for meal in weekly_meal_plan:
                if not isinstance(meal, dict):
                    return False
                    
                # 检查必要字段
                if 'day' not in meal or 'meal' not in meal or 'menu' not in meal:
                    return False
                    
                day = meal['day']
                meal_type = meal['meal']
                
                # 检查day和meal的有效性
                if not isinstance(day, int) or day < 1 or day > 7:
                    return False
                if meal_type not in ['早餐', '午餐', '晚餐']:
                    return False
                    
                # 标记该餐已存在
                meal_check[day][meal_type] = True
                
                # 检查menu结构
                menu = meal['menu']
                if not isinstance(menu, dict) or 'dishes' not in menu:
                    return False
                    
                # 检查dishes非空
                if not menu['dishes'] or not isinstance(menu['dishes'], list):
                    return False
            
            # 确保所有餐次都存在
            for day in range(1, 8):
                for meal_type in ['早餐', '午餐', '晚餐']:
                    if not meal_check[day][meal_type]:
                        return False
                        
            return True
            
        except Exception as e:
            logging.error(f"验证食谱结构时发生错误: {str(e)}")
            return False

    def _ensure_complete_meal_plan(self, weekly_meal_plan: list) -> list:
        """确保返回完整的7天21餐"""
        try:
            if self._validate_weekly_meal_plan(weekly_meal_plan):
                return weekly_meal_plan
                
            # 创建完整的食谱结构
            complete_plan = []
            meal_check = {
                day: {meal: False for meal in ['早餐', '午餐', '晚餐']}
                for day in range(1, 8)
            }
            
            # 用于检测重复的餐次
            meal_count = {}
            
            # 标记已存在的餐次
            for meal in weekly_meal_plan:
                if isinstance(meal, dict) and 'day' in meal and 'meal' in meal:
                    day = meal['day']
                    meal_type = meal['meal']
                    meal_key = f"{day}_{meal_type}"
                    
                    if isinstance(day, int) and 1 <= day <= 7 and meal_type in ['早餐', '午餐', '晚餐']:
                        # 验证菜品数据完整性
                        if not self._validate_meal_data(meal):
                            logging.warning(f"跳过无效的餐食数据: 第{day}天 {meal_type}")
                            continue
                        
                        # 检查是否已经存在该餐次
                        if meal_check[day][meal_type]:
                            logging.warning(f"检测到重复的餐次: 第{day}天 {meal_type}, 将跳过")
                            meal_count[meal_key] = meal_count.get(meal_key, 0) + 1
                            continue
                        
                        meal_check[day][meal_type] = True
                        complete_plan.append(meal)
                        meal_count[meal_key] = 1
            
            # 记录重复餐次的统计信息
            duplicates = {k: v for k, v in meal_count.items() if v > 1}
            if duplicates:
                logging.info(f"重复餐次统计: {duplicates}")
            
            # 补充缺失的餐次
            for day in range(1, 8):
                for meal_type in ['早餐', '午餐', '晚餐']:
                    if not meal_check[day][meal_type]:
                        logging.info(f"补充缺失的餐次: 第{day}天 {meal_type}")
                        complete_plan.append(self._get_default_meal_plan(day, meal_type))
            
            # 确保顺序正确
            complete_plan.sort(key=lambda x: (x['day'], ['早餐', '午餐', '晚餐'].index(x['meal'])))
            
            return complete_plan
            
        except Exception as e:
            logging.error(f"补充完整食谱时发生错误: {str(e)}")
            # 如果出错，返回完全默认的食谱
            default_plan = []
            for day in range(1, 8):
                for meal in ['早餐', '午餐', '晚餐']:
                    default_plan.append(self._get_default_meal_plan(day, meal))
            return default_plan

    def _validate_meal_data(self, meal: dict) -> bool:
        """验证单个餐食数据的完整性"""
        try:
            if not isinstance(meal, dict):
                return False
                
            # 验证基本结构
            if 'menu' not in meal or not isinstance(meal['menu'], dict):
                return False
                
            menu = meal['menu']
            if 'dishes' not in menu or not isinstance(menu['dishes'], list):
                return False
                
            # 验证每个菜品的完整性
            for dish in menu['dishes']:
                if not isinstance(dish, dict):
                    return False
                    
                # 检查必需字段
                required_fields = ['name', 'quantity', 'energy', 'introduction', 'detail']
                if not all(field in dish for field in required_fields):
                    logging.warning(f"菜品缺少必需字段: {dish.get('name', 'unknown')}")
                    return False
                    
                # 验证字段类型
                if not isinstance(dish['name'], str) or not dish['name']:
                    return False
                if not isinstance(dish['quantity'], str) or not dish['quantity']:
                    return False
                if not isinstance(dish['energy'], (int, float)):
                    return False
                if not isinstance(dish['introduction'], str) or not dish['introduction']:
                    return False
                if not isinstance(dish['detail'], list):
                    return False
                    
            return True
                
        except Exception as e:
            logging.error(f"验证餐食数据时发生错误: {str(e)}")
            return False

    def _generate_random_energy(self, meal_type: str, food_type: str = None) -> int:
        """生成合理范围内的随机能量值"""
        if food_type and food_type in DefaultMealLibrary.DISH_ENERGY_RANGES:
            min_energy, max_energy = DefaultMealLibrary.DISH_ENERGY_RANGES[food_type]
        else:
            # 根据餐次类型选择范围
            min_energy, max_energy = DefaultMealLibrary.ENERGY_RANGES.get(
                meal_type, 
                (60, 180)  # 默认范围
            )
        
        # 生成随机值，并确保是10的倍数
        return round(random.randint(min_energy, max_energy) / 10) * 10
