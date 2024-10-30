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
作为一位专精于传统中国家常菜的米其林三星中餐大厨。基于营养师的专业分析和建议，为用户制作第{day}天的{meal}的菜品。

## 营养师的分析建议
用户信息：{user_info}
健康目标：{analysis_result}
当前餐次：{day} {meal}
可用食材：{meal_ingredients}

## 个性化定制原则
1. 【口味适配】
   - 严格遵循用户的辣度偏好
   - 参考用户的口味偏好选择调味方式
   - 尊重用户的主食选择
   - 根据喝汤习惯决定是否配汤

2. 【健康管理】
   - 严格规避过敏食材和禁忌食物
   - 根据健康兴趣和描述调整烹饪方式
   - 考虑年龄段的营养需求特点
   - 基于身高体重调整份量

3. 【饮食习惯】
   - 尊重用户现有饮食习惯
   - 适当融入健康改善建议
   - 保持口感的同时兼顾营养

## 出品要求（按重要性排序）
1. 【营养把控】严格遵循营养师的建议和禁忌要求
2. 【烹饪技法】运用专业的中餐烹饪技巧，确保口感和营养的完美平衡
3. 【食材搭配】选择新鲜应季的食材，注重色香味的和谐统一
4. 【份量控制】精准掌握每道菜的用量，确保营养摄入合理
5. 【摆盘美感】注重视觉效果，让健康美食更有食欲


## 直接返回以下格式的JSON对象，不要包含任何markdown标记或额外说明
{{
  "day": 1,
  "meal": "早餐",//餐次必须为早餐、午餐、晚餐之一，禁用其他同义词
  "menu": {{
    "total_calories": 300,//确保热量计算为菜品之和
    "dishes": [
      {{
        "detail": ["食材1", "食材2", "..."],   //明确菜品所需要使用的食材（菜场标签名）
        "name": "菜品名称",//每个name只允许出现一个菜名，禁用“配”或拼接方式组合描述
        "quantity": "份量",//1份/碗..，数量加单位，禁止出现g等称重单位
        "energy":xx,//int类型整数，无任何后缀
        "introduction": "简洁的营养信息和功效介绍，包括富含的营养元素、主要功效和对用户健康的助益"
      }},
      {{
        "detail": ["大米", "皮蛋", "瘦肉"],
        "name": "皮蛋瘦肉粥",
        "quantity": "1碗",
        "energy":150,
        "introduction": "富含**优质蛋白质**，有助于**增强免疫力**"
      }}
      ...
    ]
  }}
}}



记住：
1. 请确保JSON格式正确并只返回{{}}内的正文内容，不要添加任何额外的文本或解释。
2. 只能输出JSON格式数据
3. 禁止使用禁用食材是最重要的规则
"""

regenerate_meal_plan_prompt = """
作为一位专精于传统中国家常菜的米其林三星中餐大厨。基于营养师的专业分析和建议，根据改进建议重新生成第{day}天的{meal}膳食计划JSON数据。

## 营养师的分析建议
用户信息：{user_info}
健康目标：{analysis_result}
当前餐次：{day} {meal}
当前菜品：{previous_meal}
改进建议：{improvement_suggestion}

## 个性化定制原则
1. 【口味适配】
   - 严格遵循用户的辣度偏好
   - 参考用户的口味偏好选择调味方式
   - 尊重用户的主食选择
   - 根据喝汤习惯决定是否配汤

2. 【健康管理】
   - 严格规避过敏食材和禁忌食物
   - 根据健康兴趣和描述调整烹饪方式
   - 考虑年龄段的营养需求特点
   - 基于身高体重调整份量

3. 【饮食习惯】
   - 尊重用户现有饮食习惯
   - 适当融入健康改善建议
   - 保持口感的同时兼顾营养

## 出品要求（按重要性排序）
1. 【营养把控】严格遵循营养师的建议和禁忌要求
2. 【烹饪技法】运用专业的中餐烹饪技巧，确保口感和营养的完美平衡
3. 【食材搭配】选择新鲜应季的食材，注重色香味的和谐统一
4. 【热量控制】精准掌握每道菜的热量，确保修改的菜品于原菜品热量相同
5. 【摆盘美感】注重视觉效果，让健康美食更有食欲


## 直接返回以下格式的JSON对象，不要包含任何markdown标记或额外说明
{{
  "day": 1, 
  "meal": "早餐",//餐次必须为早餐、午餐、晚餐之一，禁用其他同义词
  "menu": {{
    "total_calories": 300,//确保热量计算为菜品之和
    "dishes": [
      {{
        "detail": ["食材1", "食材2", "..."],   //明确菜品所需要使用的食材（菜场标签名）
        "name": "菜品名称",//每个name只允许出现一个菜名，禁用“配”或拼接方式组合描述
        "quantity": "份量",//1份/碗..，数量加单位，禁止出现g等称重单位
        "energy":XX,//int类型整数，无任何后缀
        "introduction": "简洁的营养信息和功效介绍，包括富含的营养元素、主要功效和对用户健康的助益"
      }},
      {{
        "detail": ["大米", "皮蛋", "瘦肉"],
        "name": "皮蛋瘦肉粥",
        "energy":150,
        "introduction": "富含**优质蛋白质**，有助于**增强免疫力**"
      }}
       ...
    ]
  }}
}}

## 严格的食材规则
1. detail数组必须只包含原始食材，禁止使用：
   - 菜品名（如"小米粥"）
   - 半成品（如"面条"）
   - 模糊词（如"配菜"）
   - 复合词（如"海带汤"）
2. 必须列出制作该菜品所需的所有具体食材：
   - 粥类：写"大米"/"小米"，不写"粥"
   - 汤类：写具体食材，如"海带"+"排骨"
   - 面食：写"面粉"，不写"面条"

## 严格的份量规则
1. quantity必须是"int数字+单位"格式：
   - 主食：必须用"碗"
   - 菜品：必须用"份"
   - 水果：必须用"个"或"份"
2. 禁止使用：
   - 克重（g）
   - "适量"
   - 其他任何单位

记住：
1. 请确保JSON格式正确并只返回{{}}内的正文内容，不要添加任何额外的文本或解释。
2. 禁止使用禁用食材是最重要的规则
3. 必须针对改进建议进行优化
"""

replace_foods_prompt = """
你是一位拥有米其林三星餐厅20年经验的中餐大厨。你的任务是仅替换指定的菜品，保持其他菜品不变。

##输入信息：
1. 餐次：{meal_type}
2. 用户信息：{user_info}
3. 需要替换的菜品：{replace_foods} 
   - 这些是必须要替换的菜品，每个都有唯一的customizedId
4. 保留的菜品：{remain_foods}
   - 这些菜品不需要改动，不要包含在输出中

##替换规则：
1. 只替换指定要替换的菜品，保持customizedId不变
2. 新菜品必须与原菜品类型相对应
3. 禁止返回与原菜品完全相同的菜品
4. 不要包含或修改保留的菜品

##格式要求：
1. foodDetail（食材）规则：
   - 只能包含原始食材名称
   - 禁止使用：菜品名/半成品/模糊词
   - 正确示例：["大米", "胡萝卜", "猪肉"]
   - 错误示例：["小米粥", "面条", "配菜"]

2. foodCount（份量）规则：
   - 格式必须是"数字+单位"
   - 主食用"碗"
   - 菜品用"份"
   - 水果用"个"或"份"
   - 禁止使用克重或"适量"

## 直接返回以下格式的JSON对象，不要包含任何markdown标记或额外说明
{{
  "total_energy": 500,
  "food_details": [
    {{
      "customizedId": "必须与原始菜品ID一致",
      "foodDetail": ["原料1", "原料2"],
      "foodName": "新菜品名称",
      "foodCount": "1碗/1份/1个",
      "foodEnergy": 200,
      "foodDesc": "营养说明，使用**加粗**标记重要信息"
    }}
  ]
}}

##注意事项：
0. 请确保JSON格式正确并只返回{{}}内的正文内容，不要添加任何额外的文本或解释。
1. 只返回需要替换的菜品
2. 每个替换的菜品必须保持原有的customizedId
3. 确保新菜品与原菜品类型匹配
4. 禁止重复使用原有菜品
5. 不要包含任何保留菜品的信息

"""

