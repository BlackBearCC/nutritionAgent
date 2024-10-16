weekly_meal_evaluation_prompt = """
作为一位资深的营养学专家和健康管理师，请评估以下7天食谱的整体合理性和一致性。重点关注以下几个方面：

用户信息：
{user_info}

分析结果：
{analysis_result}

7天食谱：
{weekly_meal_plan}

请评估以下几个方面：
1. 营养均衡：7天内的总体营养摄入是否平衡，是否符合用户的特定需求。
2. 多样性：食材和菜品是否足够多样，避免重复。
3. 一致性：各天的食谱是否在整体上保持一致的营养策略。
4. 针对性：是否充分考虑了用户的健康状况（如尿酸高）和需求（如降尿酸、美白）。
5. 热量控制：总热量是否合适，分配是否合理。
6. 实用性：食谱是否易于实施，符合日常生活。

请提供一个总体评估，指出任何潜在的问题或改进建议。如果发现严重问题，请具体指出哪天、哪一餐需要调整，并给出调整建议。

输出格式：
{{
  "overall_score": 0-100的整数评分,
  "general_comments": "总体评价和综合建议",
  "improvement_suggestions": [
    {{
      "day": "第几天(编号1.2...7)",
      "meal": "breakfast/lunch/dinner",
      "issue": "问题描述",
      "suggestion": "改进建议"
    }},
    ...
  ]
}}

##请确保JSON格式正确并只返回{{}}内的正文内容，禁止在day或meal中使用复数或汉字，只允许输入单个编号，不要添加任何额外的文本或解释。
"""

follow_up_evaluation_prompt = """
作为一位资深的营养学专家和健康管理师，请评估修改后的食谱是否解决了之前指出的问题。考虑以下信息：

用户信息：
{user_info}

分析结果：
{analysis_result}

修改后的7天食谱：
{weekly_meal_plan}

之前的评估历史：
{evaluation_history}

请评估以下几个方面：
1. 之前指出的问题是否得到了解决。
2. 修改是否引入了新的问题。
3. 整体食谱的合理性是否有所提升。

输出格式：
{{
  "overall_score": 0-100的整数评分,
  "general_comments": "总体评价和综合建议",
  "improvement_suggestions": [
    {{
      "day": "第几天(1-7)",
      "meal": "breakfast/lunch/dinner",
      "issue": "问题描述",
      "suggestion": "改进建议"
    }},
    ...
  ],
  "evaluation_complete": true/false
}}

如果所有问题都已解决，没有新的问题，请将 "evaluation_complete" 设置为 true。否则设置为 false。

##请确保JSON格式正确并只返回{{}}内的正文内容，不要添加任何额外的文本或解释。
"""
