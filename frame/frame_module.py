from base.base_agent_module import BaseAgentModule
from frame import frame_prompt
import logging
import json
import datetime
from frame.default_meal_library import DefaultMealLibrary


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
                llm_name="qwen-turbo",
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
