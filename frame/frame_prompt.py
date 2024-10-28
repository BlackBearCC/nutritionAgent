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
      "早餐": ["食材1", "食材2", "..."],//明确要使用的食材（菜场用的标签名）
      "午餐": ["食材1", "食材2", "..."],
      "晚餐": ["食材1", "食材2", "..."]
    }},
    "2": {{
      "早餐": ["食材1", "食材2", "..."],
      "午餐": ["食材1", "食材2", "..."],
      "晚餐": ["食材1", "食材2", "..."]
    }},
    ...
    "7": {{
      "早餐": ["食材1", "食材2", "..."],
      "午餐": ["食材1", "食材2", "..."],
      "晚餐": ["食材1", "食材2", "..."]
    }}
  }},
  "forbidden_ingredients": ["禁用食材1", "禁用食材2", "..."]
}}

请确保JSON格式正确并只返回{{}}内的正文内容，不要添加任何额外的文本或解释。特别注意用户的健康状况。
"""

meal_plan_prompt = """
作为一位经验丰富的中国营养师，请根据以下信息为用户制定第{day}天的{meal}膳食计划：

用户信息：
{user_info}
健康目标：
{analysis_result}
当餐可用的食材：
{meal_ingredients}

严格遵循以下规则：
1. 菜品设计规则：
   - 每个菜品必须独立列出，禁止在一个name中包含多个菜品
   - 禁止使用"+"、"、"、"/"等任何符号组合多个菜品
   - 需要搭配的菜品（如米饭配菜）必须分开独立条目列出
   - 每个菜品名称必须具体明确，禁止使用模糊描述（如"配菜"、"小菜"）

2. 份量规则：
   - quantity必须是明确的"数字+单位"格式（如"1碗"、"2个"）
   - 禁止使用克重单位（g）
   - 禁止使用"适量"等模糊描述
   - 主食类统一使用"碗"作为单位
   - 菜品类统一使用"份"作为单位
   - 水果类使用"个"或"份"作为单位

3. 营养与健康规则：
   - 严格避免使用禁用食材和过敏食材
   - 确保菜品符合用户的饮食偏好和健康目标
   - 使用**加粗**标记对用户有益的营养元素和功效
   - 确保菜品易于制作，美味常见，避免重复
   - 每个菜品的introduction必须简洁明了

请以JSON格式返回，结构如下：
{{
  "day": {day},
  "meal": "{meal}",
  "menu": {{
    "total_calories": "整数",
    "dishes": [
      {{
        "detail": ["食材1", "食材2", "..."],   //明确菜品所需要使用的食材（菜场标签名）
        "name": "菜品名称",
        "quantity": "份量（1份/碗..，数量加单位，禁止出现g等称重单位）",
        "introduction": "简洁的营养信息和功效介绍，包括富含的营养元素、主要功效和对用户健康的助益"
      }},

      {{
        "detail": ["猪里脊肉",  "木耳"],//明确要使用的食材（菜场用的标签名）
        "name": "木耳炒肉", // 单个具体菜品
        "quantity": "1份", // 明确的数字+单位
        "introduction": "富含**优质蛋白质**和**膳食纤维**，有助于**增强免疫力**"
      }},
      {{
        "detail": ["豆腐"],  // ✓ 正确：即使只有一种食材也要列出
        "name": "家常豆腐",  // ✓ 正确的菜品名称
        "quantity": "1份",
        "introduction": "富含**植物蛋白**，有助于**降低胆固醇**"
      }}
    ]
  }}
}}

错误示例：
❌ "detail": ["木耳炒肉"]  // 错误：把菜名当作食材
❌ "detail": ["木耳"]  // 错误：列出了不完整食材
❌ "name": "豆腐+木耳+胡萝卜"  // 错误：多个食材组合成菜名
❌ "name": "炒青菜配米饭"  // 错误：多个菜品组合
❌ "name": "时令蔬菜"  // 错误：模糊的菜品描述
❌ "quantity": "适量"  // 错误：不明确的份量
❌ "quantity": "100g"  // 错误：使用克重单位
❌ "detail": ["配菜"]  // 错误：模糊的食材描述

请确保严格按照以上格式输出，不要添加任何额外说明。每个菜品必须具体且独立，份量必须明确统一。
请确保JSON格式正确并只返回{{}}内的正文内容，不要添加任何额外的文本或解释。
"""

regenerate_meal_plan_prompt = """
作为一位经验丰富的中国营养师，请根据以下信息重新制定第{day}天的{meal}膳食计划：

健康目标：
{analysis_result}

用户信息：
{user_info}

上次生成的结果：
{previous_meal}

改进建议：
{improvement_suggestion}

严格遵循以下规则：
1. 菜品设计规则：
   - 每个菜品必须独立列出，禁止在一个name中包含多个菜品
   - 禁止使用"+"、"、"、"/"等任何符号组合多个菜品
   - 需要搭配的菜品（如米饭配菜）必须分开独立条目列出
   - 每个菜品名称必须具体明确，禁止使用模糊描述（如"配菜"、"小菜"）
   - 必须针对改进建议中提到的问题进行优化

2. 份量规则：
   - quantity必须是"数字+单位"格式（如"1碗"、"2个"）
   - 禁止使用克重单位（g）和"适量"
   - 主食统一用"碗"，菜品用"份"，水果用"个"或"份"

3. 营养与健康规则：
   - 严格避免使用禁用食材和过敏食材
   - 确保符合用户饮食偏好和健康目标
   - 确保每餐符合中国居民的传统饮食习惯和符合用户口味
   - 使用**加粗**标记营养元素和功效
   - introduction必须简洁明了
   - 特别注意解决改进建议中提到的问题

JSON格式示例：
{{
  "day": {day},
  "meal": "{meal}",  // 只能是"早餐"、"午餐"、"晚餐"
  "menu": {{
    "total_calories": 500,  // 整数类型
    "dishes": [
      {{
        "detail": ["食材1", "食材2", "..."],   //明确菜品所需要使用的食材（菜场标签名）
        "name": "菜品名称",
        "quantity": "份量（1份/碗..，数量加单位，禁止出现g等称重单位）",
        "introduction": "简洁的营养信息和功效介绍，包括富含的营养元素、主要功效和对用户健康的助益"
      }},
      {{
        "detail": ["猪里脊肉",  "木耳"],//明确要使用的食材（菜场用的标签名）
        "name": "木耳炒肉", // 单个具体菜品
        "quantity": "1份", // 明确的数字+单位
        "introduction": "富含**优质蛋白质**和**膳食纤维**，有助于**增强免疫力**"
      }},      
    ]
  }}
}}

错误示例：
❌ "detail": ["木耳炒肉"]  // 错误：把菜名当作食材
❌ "detail": ["木耳"]  // 错误：列出了不完整食材
❌ "name": "豆腐+木耳+胡萝卜"  // 错误：多个食材组合成菜名
❌ "name": "炒青菜配米饭"  // 错误：多个菜品组合
❌ "name": "时令蔬菜"  // 错误：模糊的菜品描述
❌ "quantity": "适量"  // 错误：不明确的份量
❌ "quantity": "100g"  // 错误：使用克重单位
❌ "detail": ["配菜"]  // 错误：模糊的食材描述

请确保JSON格式正确，只返回JSON内容，不要添加任何说明。
"""

replace_foods_prompt = """
作为一位专业的营养师，请根据以下信息为用户重新设计一份营养均衡的餐食：

餐次：{meal_type}

{user_info}

需要替换的菜品：
{replace_foods}

保留的菜品：
{remain_foods}

请遵循以下步骤：
0. 依据用户个人信息（身高、体重、年龄、性别）、饮食规则、饮食偏好，更换与待更换餐次营养元素、食品属性搭配（例如主食、饮品、炒菜菜、蔬菜、水果、坚果等属性）、热量、分量相近的一餐菜谱
1. 仅针对需要替换的食物提供新的替代方案
2. 择合适的替代食材与菜品
3. 考虑用户的饮食禁忌和过敏情况
4. 遵循用户的口味偏好和饮食习惯
5. 注意食材的口感搭配
6. 估算新替代菜品的热量，并计入总热量
7. 为替代的菜品提供简洁的营养信息和功效介绍，使用**加粗**标记对用户营养兴趣标签有益的营养元素，使用**高亮**标记描述菜品功效的词语。

请以JSON格式输出结果，仅包含替换后的新食谱部分：
{{
  "total_energy": 整数类型的总热量（包含新替换的食物和保留的食物）,
  "food_details": [
    {{
      "customizedId": 替换前食物的customizedId,  // 保持与原始食物相同的ID
      "foodDetail": ["食材1", "食材2", "..."],  //明确菜品所需要使用的食材（菜场标签名）
      "foodName": "替换后的食物名称",
      "foodCount": "份量（如：1份、1碗等）",
      "foodDesc": "简洁的营养信息和功效介绍，使用**加粗**标记重要营养元素和功效"
    }},
    ...
  ]
}}

严格遵循以下规则：
1. 菜品设计规则：
   - 每个菜品必须独立列出，禁止在一个name中包含多个菜品
   - 禁止使用"+"、"、"、"/"等任何符号组合多个菜品
   - 需要搭配的菜品（如米饭配菜）必须分开独立条目列出
   - 每个菜品名称必须具体明确，禁止使用模糊描述（如"配菜"、"小菜"）
   - 必须针对改进建议中提到的问题进行优化

2. 份量规则：
   - quantity必须是"数字+单位"格式（如"1碗"、"2个"）
   - 禁止使用克重单位（g）和"适量"
   - 主食统一用"碗"，菜品用"份"，水果用"个"或"份"

注意事项：
1. 只返回替换后的新食谱部分
2. 严格遵循用户的饮食禁忌和过敏限制
3. 符合用户的口味偏好和饮食习惯
4. 确保JSON格式正确，可直接被json.loads解析，不要添加任何额外的文本或解释
5. 返回内容禁止包含保留的无需替换的食谱
6. 必须确保每个替换后的食物都保持原始的customizedId
"""
