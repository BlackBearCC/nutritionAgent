import random
from typing import List, Dict

class DefaultMealLibrary:
    # 主食库
    STAPLE_FOODS = [
        {
            "detail": ["大米"],
            "name": "白米饭",
            "quantity": "1碗",
            "energy": 200,
            "introduction": "优质碳水化合物来源，提供持久能量"
        },
        {
            "detail": ["燕麦"],
            "name": "燕麦粥",
            "quantity": "1碗",
            "energy": 150,
            "introduction": "富含膳食纤维，有助于**稳定血糖**"
        },
        {
            "detail": ["小米"],
            "name": "小米粥",
            "quantity": "1碗",
            "energy": 180,
            "introduction": "富含**矿物质**，易于消化吸收"
        },
        {
            "detail": ["面粉", "鸡蛋"],
            "name": "全麦面包",
            "quantity": "2片",
            "energy": 160,
            "introduction": "含有丰富的**B族维生素**和膳食纤维"
        }
    ]

    # 蛋白质库
    PROTEIN_FOODS = [
        {
            "detail": ["鸡胸肉"],
            "name": "清蒸鸡胸",
            "quantity": "1份",
            "energy": 180,
            "introduction": "优质瘦肉蛋白，低脂高蛋白"
        },
        {
            "detail": ["豆腐", "木耳"],
            "name": "木耳豆腐",
            "quantity": "1份",
            "energy": 120,
            "introduction": "植物蛋白搭配，有助于**降低胆固醇**"
        },
        {
            "detail": ["鸡蛋", "西红柿"],
            "name": "西红柿炒蛋",
            "quantity": "1份",
            "energy": 160,
            "introduction": "优质蛋白与维生素C的绝佳搭配"
        }
    ]

    # 蔬菜库
    VEGETABLE_FOODS = [
        {
            "detail": ["西兰花"],
            "name": "清炒西兰花",
            "quantity": "1份",
            "energy": 80,
            "introduction": "富含**维生素C**和膳食纤维"
        },
        {
            "detail": ["菠菜"],
            "name": "清炒菠菜",
            "quantity": "1份",
            "energy": 60,
            "introduction": "补铁佳品，富含**叶酸**"
        },
        {
            "detail": ["胡萝卜", "青椒"],
            "name": "炒时蔬",
            "quantity": "1份",
            "energy": 70,
            "introduction": "维生素A和C的良好来源"
        }
    ]

    # 汤品库
    SOUP_FOODS = [
        {
            "detail": ["冬瓜", "排骨"],
            "name": "冬瓜排骨汤",
            "quantity": "1碗",
            "energy": 120,
            "introduction": "清淡营养，利水消肿"
        },
        {
            "detail": ["番茄", "蛋"],
            "name": "番茄蛋汤",
            "quantity": "1碗",
            "energy": 100,
            "introduction": "开胃解腻，补充**维生素C**"
        }
    ]

    @classmethod
    def get_default_meal_plan(cls, day: int, meal: str) -> dict:
        """生成带有随机性的默认膳食计划"""
        meal_energy_ranges = {
            "早餐": (400, 500),
            "午餐": (600, 700),
            "晚餐": (500, 600)
        }
        
        dishes = []
        total_energy = 0
        
        # 早餐搭配
        if meal == "早餐":
            dishes.append(random.choice(cls.STAPLE_FOODS))
            dishes.append(random.choice(cls.PROTEIN_FOODS))
            if random.random() > 0.5:  # 50%概率添加蔬菜
                dishes.append(random.choice(cls.VEGETABLE_FOODS))
                
        # 午餐和晚餐搭配
        else:
            dishes.append(random.choice(cls.STAPLE_FOODS))
            dishes.append(random.choice(cls.PROTEIN_FOODS))
            dishes.append(random.choice(cls.VEGETABLE_FOODS))
            if random.random() > 0.3:  # 70%概率添加汤
                dishes.append(random.choice(cls.SOUP_FOODS))
        
        total_energy = sum(dish["energy"] for dish in dishes)
        
        return {
            "day": day,
            "meal": meal,
            "menu": {
                "total_calories": total_energy,
                "dishes": dishes
            }
        }

    @classmethod
    def get_default_ingredients(cls) -> dict:
        """生成默认的食材推荐"""
        basic_ingredients = [
            "大米", "面粉", "燕麦", "小米",  # 主食类
            "鸡胸肉", "豆腐", "鸡蛋", "瘦猪肉",  # 蛋白质类
            "西兰花", "菠菜", "胡萝卜", "西红柿", "青椒",  # 蔬菜类
            "木耳", "香菇"  # 菌菇类
        ]
        
        common_forbidden = ["海鲜", "坚果", "蛋糕", "油炸食品", "含糖饮料"]
        
        recommended = {}
        for day in range(1, 8):
            recommended[str(day)] = {
                meal: random.sample(basic_ingredients, 6)  # 随机选择6种食材
                for meal in ["早餐", "午餐", "晚餐"]
            }
            
        return {
            "recommended_ingredients": recommended,
            "forbidden_ingredients": common_forbidden
        }
