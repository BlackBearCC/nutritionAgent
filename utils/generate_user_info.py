import random
from datetime import datetime, timedelta

def generate_user_info():
    # 身高
    height = random.randint(140, 190)
    
    # 体重
    weight = round(random.uniform(50, 200), 1)
    
    # 性别
    gender = random.choice(['男', '女'])
    
    # 生日
    current_year = datetime.now().year
    birth_year = random.choices([random.randint(current_year - 80, current_year - 12), random.randint(current_year - 40, current_year - 18)], weights=[0.6, 0.4])[0]
    birth_date = datetime(birth_year, random.randint(1, 12), random.randint(1, 28))
    age = current_year - birth_year
    
    # 健康兴趣
    health_interests = random.sample([
        "美白提亮", "淡化色斑", "控油祛痘", "细腻皮肤", "告别水肿",
        "皮炎改善", "强化口腔健康", "促进消化", "强壮骨骼", "强韧发质",
        "易敏体质改变", "熬夜后补救", "缓解眼疲劳", "摆脱焦虑", "告别失眠"
    ], k=random.randint(1, 3))
    
    # 饮食禁忌
    dietary_restrictions = random.sample(["素食", "蛋奶素食", "不吃猪肉"], k=random.randint(0, 2))
    
    # 食物过敏
    food_allergies = random.choice([["无"], random.sample(["海鲜", "坚果", "花生", "甲壳类水生动物", "鸡蛋", "大豆类", "乳制品"], k=random.randint(1, 3))])
    
    # 口味偏好
    taste_preferences = random.choice([["都可以"], random.sample(["江浙沪", "西北", "东北", "川湘", "云贵", "京津", "山东", "粤"], k=random.randint(1, 3))])
    
    # 主食偏好
    staple_preferences = random.choice([["都可以"], random.sample(["面食及面点", "粥", "米饭", "米粉", "肠粉"], k=random.randint(1, 3))])
    
    # 吃辣
    spicy_preference = random.choice(["能吃辣", "不能吃辣"])
    
    # 喝汤习惯
    soup_habit = random.choice(["有喝汤习惯", "无喝汤习惯"])
    
    user_info = f"""
    用户信息：
    性别：{gender}，年龄：{age}岁，身高：{height}厘米，体重：{weight}千克
    出生日期：{birth_date.strftime('%Y年%m月%d日')}
    健康兴趣：{', '.join(health_interests)}
    饮食禁忌：{', '.join(dietary_restrictions) if dietary_restrictions else '无'}
    食物过敏：{', '.join(food_allergies)}
    口味偏好：{', '.join(taste_preferences)}
    主食偏好：{', '.join(staple_preferences)}
    辣度偏好：{spicy_preference}
    喝汤习惯：{soup_habit}
    """
    
    return user_info
