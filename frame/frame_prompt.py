ingredient_generation_prompt = """
作为一位营养专家，请根据以下信息为用户的每日每餐生成适合的食材列表，并提供一个统一的禁用食材列表：

健康目标：
{analysis_result}

用户信息：
{user_info}

参考食材库：
{food_database}

请遵循以下步骤：
1. 根据健康目标和用户信息，选择适合的食材和确定禁用食材。
2. 考虑用户的健康状况、营养需求和可能的饮食限制（如尿酸高）。
3. 参考可用食材生成更多食材，若无参考食材则根据步骤1推理食材，分为21组，每组代表7天每天3餐的食材。
4. 确保每组食材都能满足一餐的营养需求，符合用户口味，符合中国居民饮食习惯，并且21餐的食材有足够的变化。
5. 为每餐列出5-8种推荐食材。
6. 根据用户病情，主诉，禁忌/过敏食品，提供一个统一的禁用食材列表。

请以JSON格式输出结果，结构如下：
{{
  "recommended_ingredients": {{
    "1": {{
      "breakfast": ["食材1", "食材2", "..."],
      "lunch": ["食材1", "食材2", "..."],
      "dinner": ["食材1", "食材2", "..."]
    }},
    "2": {{
      "breakfast": ["食材1", "食材2", "..."],
      "lunch": ["食材1", "食材2", "..."],
      "dinner": ["食材1", "食材2", "..."]
    }},
    ...
    "7": {{
      "breakfast": ["食材1", "食材2", "..."],
      "lunch": ["食材1", "食材2", "..."],
      "dinner": ["食材1", "食材2", "..."]
    }}
  }},
  "forbidden_ingredients": ["禁用食材1", "禁用食材2", "..."]
}}

请确保JSON格式正确并只返回{{}}内的正文内容，不要添加任何额外的文本或解释。特别注意用户的健康状况。
"""

meal_plan_prompt = """
作为一位经验丰富的中国营养师，请根据以下信息为用户制定第{day}天的{meal}膳食计划，确保符合中国人的饮食习惯，符合用户信息的各种饮食偏好，符合健康目标要求：
用户信息：
{user_info}
健康目标：
{analysis_result}
当餐可用的食材：
{meal_ingredients}
请遵循以下步骤：
1.根据用户信息和健康目标，平衡食材和烹饪方式，为指定的膳食设计适当的菜品，避免使用forbidden_ingredients。
2.以当餐提供的推荐食材为主食材制作菜品，确保每餐符合中国居民的传统饮食习惯和符合用户口味。
3.严格避免使用禁用食材列表中的食材，禁用任何用户信息中的禁忌/过敏食材用于食谱。
4.注意食材之间的搭配，以达到最佳的营养效果和口感。
5.考虑口感的多样性，包括软、硬、脆、嫩等不同质地。
6.估算每餐的热量。
7.为每个菜品提供简洁的营养信息和功效介绍，使用**加粗**标记对用户营养兴趣标签有益的营养元素，菜品功效的词语。

请以JSON格式输出结果，结构如下：
{{
  "day": {day},
  "meal": "{meal}",
  "menu": {{
    "total_calories": "XX（整数类型）",
    "dishes": [
      {{
        "name": "菜品名称",
        "quantity": "份量（1份/碗..，数量加单位，禁止出现g等称重单位）",
        "introduction": "简洁的营养信息和功效介绍，包括富含的营养元素、主要功效和对用户健康的助益"
      }},
      {{
        "name": "菜品名称",
        "quantity": "份量",
        "introduction": "简洁的营养信息和功效介绍"
      }},
      ...
    ]
  }}
}}

请确保JSON格式正确并只返回{{}}内的正文内容，不要添加任何额外的文本或解释。每餐的菜品应符合中国传统饮食习惯，同时考虑用户的健康需求。菜品介绍应简洁明了，突出重点营养信息和功效。
"""

regenerate_meal_plan_prompt = """
作为一位经验丰富的中国营养师，请根据以下信息为用户重新制定第{day}天的{meal}膳食计划，确保符合中国人的饮食习惯，符合用户口味，符合健康目标要求：

健康目标：
{analysis_result}

用户信息：
{user_info}


上次生成的结果：
{previous_meal}

改进建议：
{improvement_suggestion}

请遵循以下步骤：
1. 根据用户信息和健康目标，平衡食材和烹饪方式，为指定的膳食重新设计适当的菜品。
2. 以当餐提供的推荐食材为主食材制作菜品，确保符合中国居民的传统饮食习惯和用户口味。
3. 严格避免使用禁用食材列表中的食材，禁用任何用户信息中的禁忌/过敏食材用于食谱。
4. 注意食材之间的搭配，以达到最佳的营养效果和口感。
5. 考虑口感的多样性，包括软、硬、脆、嫩等不同质地。
6. 估算每餐的热量。
7. 为每个菜品提供简洁的营养信息和功效介绍，使用**加粗**标记对用户营养兴趣标签有益的营养元素，使用**高亮**标记描述菜品功效的词语。
8. 特别注意解决改进建议中提到的问题。

请以JSON格式输出结果，结构如下：
{{
  "day": {day},
  "meal": "{meal}",
  "menu": {{
    "total_calories": "XX（整数类型）",
    "dishes": [
      {{
        "name": "菜品名称",
        "quantity": "份量（1份/碗..，数量加单位，禁止出现g等称重单位）",
        "introduction": "简洁的营养信息和功效介绍，包括富含的营养元素、主要功效和对用户健康的助益"
      }},
      {{
        "name": "菜品名称",
        "quantity": "份量",
        "introduction": "简洁的营养信息和功效介绍"
      }},
      ...
    ]
  }}
}}

请确保JSON格式正确并只返回{{}}内的正文内容，不要添加任何额外的文本或解释。每餐的菜品应符合中国传统饮食习惯，同时考虑用户的健康需求和改进建议。菜品介绍应简洁明了，突出重点营养信息和功效。
"""

nutrition_allocation_prompt = """
作为营养专家，请根据以下分析结果和用户信息为用户的三餐分配营养。请考虑用户的总体营养需求和健康状况。

分析结果：
{input_text}

用户信息：
{user_info}

请为早餐、午餐和晚餐分配营养。每餐应包括蛋白质、碳水化合物和脂肪的具体克数。同时，请10-20字简要说明分配理由。
"""

food_selection_prompt = """
作为营养专家，请根据以下营养分配、用户信息和可用食材库为用户选择具体食材。

营养分配：
{input_text}

用户信息：
{user_info}

可用食材库：
{food_database}

请为早餐、午餐和晚餐选择合适的食材。每餐选择5-12种食材，并简要说明选择理由。请确保选择的食材在提供的食材库中，并能满足营养分配的要求。
"""

cooking_method_prompt = """
作为烹饪专家，请根据以下营养分配和选定的食材，推荐适当的烹饪方式。考虑到营养保留、口感和健康因素。

营养分配：
{input_text}

选定的食材：
{food_selection}

请为早餐、午餐和晚餐推荐清蒸/红烧等各种烹饪方式，并10-20字简要说明推荐原因。请确保烹饪方式适合选定的食材，并有助于实现预期的营养目标。
"""

daily_meal_validation_prompt = """
作为一位营养专家，请审核并调整第{day}天的三餐计划，确保其合理性和多样性：

分析结果：
{analysis_result}

用户信息：
{user_info}

当天三餐计划：
{day_meals}

请遵循以下步骤：
1. 审核三餐是否符合用户的营养需求和健康状况。
2. 检查三餐之间的多样性，避免重复的食材或烹饪方式。
3. 确保每餐的热量分配合理。
4. 如果发现问题，请直接调整菜品，使其更加合理和多样化。
5. 保持中国传统饮食习惯。

请以JSON格式输出调整后的三餐计划，结构如下：
[
  {{
    "day": {day},
    "meal": "breakfast",
    "menu": {{
      "total_calories": "XXKcal",
      "dishes": [
        {{
          "name": "菜品名称",
          "quantity": "份量（1份/碗，数量加单位，禁止出现g等称重单位）"
        }},
        ...
      ]
    }}
  }},
  {{
    "day": {day},
    "meal": "lunch",
    "menu": {{
      "total_calories": "XXKcal",
      "dishes": [
        {{
          "name": "菜品名称",
          "quantity": "份量"
        }},
        ...
      ]
    }}
  }},
  {{
    "day": {day},
    "meal": "dinner",
    "menu": {{
      "total_calories": "XXKcal",
      "dishes": [
        {{
          "name": "菜品名称",
          "quantity": "份量"
        }},
        ...
      ]
    }}
  }}
]

请确保JSON格式正确并只返回[]内的正文内容，不要添加任何额外的文本或解释。
"""

