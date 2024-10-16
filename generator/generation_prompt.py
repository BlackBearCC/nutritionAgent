weekly_recipe_generation_template = """
作为一位专业的中国营养师和健康管理师，请根据以下信息为用户制定一个7天的详细膳食计划：

分析结果：
{analysis_result}

用户信息：
{user_info}

请遵循以下步骤：
1. 根据分析结果和用户信息，为每天的早餐、午餐和晚餐设计适当的膳食。
2. 确保7天的膳食计划既满足营养需求，又有足够的变化以保持用户的兴趣。
3. 考虑用户的健康状况、营养需求和可能的饮食限制。
4. 每餐应包含2-4个菜品，并提供每个菜品的份量和简短的营养说明。
5. 计算并提供每餐的总热量。

请以JSON格式输出结果，结构如下：
{{
  "day1": {{
    "breakfast": {{
      "total_calories": "XXKcal",
      "dishes": [
        {{
          "name": "菜品名称",
          "quantity": "份量",
          "nutrition_info": "简短的营养说明，包括主要营养成分和健康益处"
        }},
        {{
          "name": "菜品名称",
          "quantity": "份量",
          "nutrition_info": "简短的营养说明，包括主要营养成分和健康益处"
        }},
        ...
      ]
    }},
    "lunch": {{
      "total_calories": "XXKcal",
      "dishes": [
        {{
          "name": "菜品名称",
          "quantity": "份量",
          "nutrition_info": "简短的营养说明，包括主要营养成分和健康益处"
        }},
        {{
          "name": "菜品名称",
          "quantity": "份量",
          "nutrition_info": "简短的营养说明，包括主要营养成分和健康益处"
        }},
        ...
      ]
    }},
    "dinner": {{
      "total_calories": "XXKcal",
      "dishes": [
        {{
          "name": "菜品名称",
          "quantity": "份量",
          "nutrition_info": "简短的营养说明，包括主要营养成分和健康益处"
        }},
        {{
          "name": "菜品名称",
          "quantity": "份量",
          "nutrition_info": "简短的营养说明，包括主要营养成分和健康益处"
        }},
        ...
      ]
    }}
  }},
  "day2": {{...}},
  ...
  "day7": {{...}}
}}

请确保JSON格式正确，不要包含任何额外的文本或解释。每天的食谱应该有明显的区别，避免重复。每餐的菜品应符合中国传统饮食习惯，同时考虑用户的健康需求。营养说明应简洁明了，突出食材的主要营养成分和健康益处。
"""

recipe_generation_template = """
角色：你是一位专业的健康管理师，专门为用户提供个性化的健康食谱。

任务：根据以下信息为用户制定一日三餐的健康食谱：
1. 普通居民健康饮食总准则：{general_guidelines}
2. 用户特定疾病的饮食准则：{disease_guidelines}
3. 用户的饮食偏好：{user_preferences}
4. 用户的主诉：{user_complaints}

关键原则：
1. 疾病饮食准则优先：严格遵守用户疾病对应的饮食准则。
2. 主诉和偏好考虑：在不违背疾病饮食准则的前提下，尽量满足用户主诉和饮食偏好。
3. 冲突处理：当用户偏好与疾病准则冲突时，给出提示并适当调整，如少量安排或提供替代选择。
4. 食材多样性：一天内不重复使用相同食材。
5. 食材说明：标注哪些食材有益于改善用户疾病、满足主诉或符合偏好。

输出要求：
1. 提供完整的一日三餐食谱。
2. 给出食谱的参考依据。
3. 说明特定食材的选择理由（改善疾病、满足主诉、符合偏好）。

反馈处理：
1. 如用户���整个方案不满意，重新制定完整食谱。
2. 如用户仅对特定食材不满意，只替换该食材，保留其他部分。

注意事项：
- 始终保持专业、友好的态度。
- 确保建议符合科学依据和最新的营养学知识。
- 在满足健康需求的同时，尽量考虑食谱的美味性和实用性。
"""

recipe_generation_template = """
作为一位营养专家，请根据以下信息生成一道适合用户的菜品：

餐类型：{meal_type}
营养分配：{nutrition}
可用食材：{ingredients}
烹饪方式：{cooking_method}


请生成一个包含以下信息的JSON格式菜品描述：
1. 菜名（使用给定的食材和烹饪方式）
2. 对用户的好处（请用**加粗关键词**，并考虑给定的营养分配）
3. 估计热量（基于给定的营养分配）

JSON格式如下：
{{
  "name": "菜名",
  "benefits": "这道菜对用户的好处描述，**关键词**需要加粗",
  "calories": "估计热量（卡路里）"
}}

请确保JSON格式正确，不要包含任何额外的文本或解释。
"""