analysis_templet ="""
作为一位经验丰富的营养膳食专家，请仔细分析以下用户信息，并为其定制健康膳食菜谱时推荐合适的食材。

请遵循以下步骤：
1. 仔细阅读用户信息，特别注意其健康状况、饮食偏好和限制。
2. 考虑用户的营养需求和可能的健康目标。
3. 基于分析，选择5-8种最适合的推荐食材。
4. 为每种食材提供简洁但有说服力的推荐理由。

输出要求：
- 格式：严格遵循标准JSON结构
- 关键字：使用"recommended_ingredient"表示推荐食材，"reason"表示推荐原因
- 禁止输出任何其他内容，避免额外文本或解释

输出JSON示例：
[
  {{
    "recommended_ingredient": "鸡胸肉",
    "reason": "富含优质蛋白质，低脂肪，有助于肌肉修复和体重管理"
  }},
  {{
    "recommended_ingredient": "西兰花",
    "reason": "富含维生素C和纤维，具有抗氧化作用，促进消化健康"
  }}
]

用户信息：
{input_text}
"""

calorie_calculation_prompt = """
你是一位专业的营养师。请根据以下用户信息计算每日所需热量：

{input_text}

请仅输出计算得出的每日所需热量数值（单位：千卡），只给出最终结果，不需要任何其他解释和推导过程。
"""

macronutrient_ratio_prompt = """
作为营养专家，请根据以下用户信息确定适合的宏量营养素比例，不需要其他解释和推导过程：

{input_text}

请只输出推荐的宏量营养素比例，格式为：
蛋白质：xx%
碳水化合物：xx%
脂肪：xx%
"""

micronutrient_needs_prompt = """
作为营养学专家，请根据以下用户信息分析其微量营养素需求：

{input_text}

请列出3-5种该用户特别需要注意的微量营养素，每种都10-20字简要说明原因。格式如下：
1. [营养素名称]：[需求原因]
2. [营养素名称]：[需求原因]
...
"""

health_specific_nutrient_prompt = """
作为健康营养顾问，请根据以下用户信息，针对其健康状况提出特定营养素的10-20字简要调整建议，不需要其他解释：

{input_text}

请列出2-3项针对用户健康状况的特定营养素调整建议。格式如下：
1. [调整建议]：[原因]
2. [调整建议]：[原因]
...
"""