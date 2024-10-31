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
            "introduction": "富含**优质碳水化合物**，提供**持久能量**"
        },
        {
            "detail": ["燕麦"],
            "name": "燕麦粥",
            "quantity": "1碗",
            "energy": 150,
            "introduction": "富含**膳食纤维**，有助于**稳定血糖**和**促进消化**"
        },
        {
            "detail": ["小米"],
            "name": "小米粥",
            "quantity": "1碗",
            "energy": 180,
            "introduction": "富含**矿物质**和**维生素B族**，易于**消化吸收**"
        },
        {
            "detail": ["面粉", "鸡蛋"],
            "name": "全麦面包",
            "quantity": "2片",
            "energy": 160,
            "introduction": "含有丰富的**B族维生素**和**膳食纤维**，有助于**肠道健康**"
        },
        {
            "detail": ["糙米"],
            "name": "糙米粥",
            "quantity": "1碗",
            "energy": 180,
            "introduction": "富含**膳食纤维**和**维生素B族**，有助于**控制血糖**和**改善消化**"
        },
        {
            "detail": ["红豆", "薏仁"],
            "name": "红豆薏仁粥",
            "quantity": "1碗",
            "energy": 200,
            "introduction": "具有**利水消肿**功效，富含**植物蛋白**和**膳食纤维**"
        },
        {
            "detail": ["黑米", "红枣"],
            "name": "黑米红枣粥",
            "quantity": "1碗",
            "energy": 190,
            "introduction": "**补血养颜**，改善**睡眠质量**，富含**铁质**"
        },
        {
            "detail": ["绿豆", "薏仁"],
            "name": "绿豆薏仁粥",
            "quantity": "1碗",
            "energy": 170,
            "introduction": "具有**清热消暑**功效，改善**水肿**，补充**植物蛋白**"
        },
        {
            "detail": ["藜麦", "鸡胸肉"],
            "name": "藜麦鸡胸饭",
            "quantity": "1碗",
            "energy": 220,
            "introduction": "富含**完整蛋白质**和**膳食纤维**，是**减脂增肌**的理想主食"
        },
        {
            "detail": ["紫米", "糯米"],
            "name": "紫米饭",
            "quantity": "1碗",
            "energy": 210,
            "introduction": "富含**花青素**和**矿物质**，具有**抗氧化**和**养胃**功效"
        },
        {
            "detail": ["燕麦", "红薯"],
            "name": "燕麦红薯饭",
            "quantity": "1碗",
            "energy": 220,
            "introduction": "富含**膳食纤维**和**β胡萝卜素**，有助于**控制血糖**和**护眼明目**"
        },
        {
            "detail": ["荞麦", "紫薯"],
            "name": "荞麦紫薯面",
            "quantity": "1份",
            "energy": 230,
            "introduction": "含有**芦丁**和**花青素**，具有**降血压**和**抗氧化**功效"
        },
        {
            "detail": ["玉米", "红薯", "小米"],
            "name": "三色杂粮饭",
            "quantity": "1碗",
            "energy": 215,
            "introduction": "富含**膳食纤维**和**β胡萝卜素**，具有**护眼明目**和**养胃健脾**功效"
        },
        {
            "detail": ["薏仁", "红豆", "糙米"],
            "name": "薏仁红豆饭",
            "quantity": "1碗",
            "energy": 205,
            "introduction": "具有**利水消肿**和**健脾祛湿**功效，富含**植物蛋白**"
        },
        {
            "detail": ["南瓜", "燕麦"],
            "name": "南瓜燕麦粥",
            "quantity": "1碗",
            "energy": 175,
            "introduction": "富含**膳食纤维**和**胡萝卜素**，有助于**护眼**和**改善便秘**"
        },
        {
            "detail": ["荞麦", "小米", "大米"],
            "name": "荞麦小米饭",
            "quantity": "1碗",
            "energy": 195,
            "introduction": "富含**芦丁**和**B族维生素**，有助于**降血压**和**改善失眠**"
        }
    ]

    # 蛋白质库
    PROTEIN_FOODS = [
        {
            "detail": ["鸡胸肉"],
            "name": "煎鸡胸肉",
            "quantity": "1份",
            "energy": 180,
            "introduction": "富含**优质蛋白质**和**必需氨基酸**，有助于**增肌健身**"
        },
        {
            "detail": ["三文鱼"],
            "name": "煎三文鱼",
            "quantity": "1份",
            "energy": 220,
            "introduction": "富含**omega-3脂肪酸**和**DHA**，有助于**心脑健康**"
        },
        {
            "detail": ["豆腐", "虾仁"],
            "name": "虾仁豆腐",
            "quantity": "1份",
            "energy": 160,
            "introduction": "**低脂高蛋白**，易于**消化吸收**，补充**优质蛋白**"
        },
        {
            "detail": ["鳕鱼"],
            "name": "清蒸鳕鱼",
            "quantity": "1份",
            "energy": 180,
            "introduction": "**低脂肪**，富含**优质蛋白**和**DHA**，易于**消化吸收**"
        },
        {
            "detail": ["带鱼"],
            "name": "清蒸带鱼",
            "quantity": "1份",
            "energy": 180,
            "introduction": "富含**DHA**和**EPA**，有助于**大脑发育**和**心血管健康**"
        },
        {
            "detail": ["虾仁", "西兰花"],
            "name": "西兰花炒虾仁",
            "quantity": "1份",
            "energy": 165,
            "introduction": "补充**优质蛋白**和**硒元素**，增强**免疫力**"
        },
        {
            "detail": ["黄豆芽", "毛豆"],
            "name": "清炒豆芽毛豆",
            "quantity": "1份",
            "energy": 120,
            "introduction": "富含**植物雌激素**和**维生素E**，有助于**美容养颜**"
        },
        {
            "detail": ["鹌鹑蛋", "青椒"],
            "name": "青椒鹌鹑蛋",
            "quantity": "6个",
            "energy": 155,
            "introduction": "富含**卵磷脂**和**维生素C**，提高**免疫力**"
        },
        {
            "detail": ["鳕鱼", "西兰花"],
            "name": "清蒸鳕鱼西兰花",
            "quantity": "1份",
            "energy": 185,
            "introduction": "富含**优质蛋白**和**DHA**，有助于**大脑发育**和**视力保护**"
        },
        {
            "detail": ["牛里脊", "蘑菇"],
            "name": "蘑菇牛肉",
            "quantity": "1份",
            "energy": 210,
            "introduction": "富含**铁质**和**锌**，提供**优质蛋白**，增强**免疫力**"
        },
        {
            "detail": ["鸡胸肉", "芦笋"],
            "name": "芦笋鸡胸",
            "quantity": "1份",
            "energy": 175,
            "introduction": "**低脂高蛋白**，富含**叶酸**，适合**减脂增肌**"
        }
    ]

    # 蔬菜库
    VEGETABLE_FOODS = [
        {
            "detail": ["西兰花"],
            "name": "清炒西兰花",
            "quantity": "1份",
            "energy": 70,
            "introduction": "富含**维生素C**和**膳食纤维**，具有**抗氧化**功效"
        },
        {
            "detail": ["菠菜"],
            "name": "清炒菠菜",
            "quantity": "1份",
            "energy": 55,
            "introduction": "富含**铁质**和**叶酸**，有助于**补血养颜**"
        },
        {
            "detail": ["胡萝卜", "木耳"],
            "name": "胡萝卜木耳",
            "quantity": "1份",
            "energy": 65,
            "introduction": "补充**胡萝卜素**，有助于**护眼明目**和**美容养颜**"
        },
        {
            "detail": ["芦笋"],
            "name": "清炒芦笋",
            "quantity": "1份",
            "energy": 45,
            "introduction": "富含**叶酸**和**芦丁**，有助于**抗衰老**和**美容养颜**"
        },
        {
            "detail": ["秋葵"],
            "name": "清炒秋葵",
            "quantity": "1份",
            "energy": 35,
            "introduction": "富含**膳食纤维**和**黏蛋白**，具有**降血糖**功效"
        },
        {
            "detail": ["菜心"],
            "name": "清炒菜心",
            "quantity": "1份",
            "energy": 40,
            "introduction": "富含**叶酸**和**维生素K**，有助于**补铁**和**骨骼健康**"
        },
        {
            "detail": ["紫甘蓝"],
            "name": "凉拌紫甘蓝",
            "quantity": "1份",
            "energy": 50,
            "introduction": "富含**花青素**和**维生素C**，具有**抗氧化**和**增强免疫**功效"
        },
        {
            "detail": ["菜花", "胡萝卜"],
            "name": "炒双花",
            "quantity": "1份",
            "energy": 60,
            "introduction": "富含**维生素C**和**胡萝卜素**，增强**免疫力**和**护眼明目**"
        },
        {
            "detail": ["油麦菜"],
            "name": "清炒油麦菜",
            "quantity": "1份",
            "energy": 45,
            "introduction": "富含**叶酸**和**铁质**，有助于**补血养颜**"
        },
        {
            "detail": ["茼蒿"],
            "name": "清炒茼蒿",
            "quantity": "1份",
            "energy": 35,
            "introduction": "富含**维生素K**和**叶黄素**，有助于**护眼**和**骨骼健康**"
        },
        {
            "detail": ["韭黄"],
            "name": "清炒韭黄",
            "quantity": "1份",
            "energy": 50,
            "introduction": "富含**胡萝卜素**和**维生素C**，具有**暖胃**功效"
        }
    ]

    # 汤品库
    SOUP_FOODS = [
        {
            "detail": ["海带", "豆腐"],
            "name": "海带豆腐汤",
            "quantity": "1碗",
            "energy": 90,
            "introduction": "补充**碘质**，调节**甲状腺**功能，富含**植物蛋白**"
        },
        {
            "detail": ["冬瓜", "排骨"],
            "name": "冬瓜排骨汤",
            "quantity": "1碗",
            "energy": 120,
            "introduction": "具有**清热利尿**功效，有助于**美容养颜**"
        },
        {
            "detail": ["山药", "红枣", "枸杞"],
            "name": "山药红枣汤",
            "quantity": "1碗",
            "energy": 110,
            "introduction": "具有**健脾养胃**和**补气养血**功效，提高**免疫力**"
        },
        {
            "detail": ["莲子", "百合", "银耳"],
            "name": "莲子百合银耳汤",
            "quantity": "1碗",
            "energy": 95,
            "introduction": "具有**养心安神**和**润肺止咳**功效，改善**睡眠质量**"
        },
        {
            "detail": ["西红柿", "蛋"],
            "name": "西红柿蛋汤",
            "quantity": "1碗",
            "energy": 95,
            "introduction": "富含**番茄红素**和**优质蛋白**，具有**抗氧化**功效"
        },
        {
            "detail": ["玉米", "排骨", "胡萝卜"],
            "name": "玉米胡萝卜排骨汤",
            "quantity": "1碗",
            "energy": 145,
            "introduction": "富含**胶原蛋白**和**胡萝卜素**，有助于**美容养颜**和**护眼明目**"
        },
        {
            "detail": ["冬瓜", "海带", "虾皮"],
            "name": "冬瓜海带汤",
            "quantity": "1碗",
            "energy": 85,
            "introduction": "具有**清热利尿**功效，补充**碘质**，促进**新陈代谢**"
        },
        {
            "detail": ["白萝卜", "牛肉"],
            "name": "萝卜牛肉汤",
            "quantity": "1碗",
            "energy": 130,
            "introduction": "具有**健胃消食**功效，补充**铁质**，增强**体质**"
        }
    ]

    # 水果库
    FRUIT_FOODS = [
        {
            "detail": ["苹果"],
            "name": "苹果",
            "quantity": "1个",
            "energy": 70,
            "introduction": "富含**膳食纤维**和**果胶**，有助于**调节肠道**"
        },
        {
            "detail": ["蓝莓"],
            "name": "蓝莓",
            "quantity": "1小碗",
            "energy": 85,
            "introduction": "富含**花青素**，具有**抗氧化**功效，保护**视力健康**"
        },
        {
            "detail": ["火龙果"],
            "name": "火龙果",
            "quantity": "1份",
            "energy": 55,
            "introduction": "富含**植物性色素**和**维生素C**，有助于**美容养颜**和**排毒养颜**"
        },
        {
            "detail": ["奇异果"],
            "name": "奇异果",
            "quantity": "2个",
            "energy": 90,
            "introduction": "富含**维生素C**和**膳食纤维**，促进**肠道健康**"
        },
        {
            "detail": ["柑橘"],
            "name": "柑橘",
            "quantity": "1个",
            "energy": 45,
            "introduction": "富含**维生素C**和**类黄酮**，增强**免疫力**"
        },
        {
            "detail": ["石榴"],
            "name": "石榴",
            "quantity": "1份",
            "energy": 75,
            "introduction": "富含**多酚**和**维生素C**，具有**抗氧化**和**美容养颜**功效"
        },
        {
            "detail": ["木瓜"],
            "name": "木瓜",
            "quantity": "1份",
            "energy": 65,
            "introduction": "富含**木瓜蛋白酶**和**维生素C**，有助于**消化**和**美容养颜**"
        },
        {
            "detail": ["杨桃"],
            "name": "杨桃",
            "quantity": "1个",
            "energy": 35,
            "introduction": "富含**维生素C**和**膳食纤维**，具有**生津止渴**功效"
        },
        {
            "detail": ["草莓"],
            "name": "草莓",
            "quantity": "10颗",
            "energy": 70,
            "introduction": "富含**维生素C**和**花青素**，具有**抗氧化**和**美白**功效"
        }
    ]

    # 新增：养生茶饮库
    HEALTHY_DRINKS = [
        {
            "detail": ["红枣", "枸杞", "桂圆"],
            "name": "红枣枸杞茶",
            "quantity": "1杯",
            "energy": 45,
            "introduction": "具有**补血养颜**和**安神助眠**功效，提升**免疫力**"
        },
        {
            "detail": ["菊花", "金银花", "绿茶"],
            "name": "清热花茶",
            "quantity": "1杯",
            "energy": 15,
            "introduction": "具有**清热明目**和**解暑降火**功效，改善**眼疲劳**"
        },
        {
            "detail": ["柠檬", "蜂蜜"],
            "name": "柠檬蜂蜜水",
            "quantity": "1杯",
            "energy": 40,
            "introduction": "富含**维生素C**和**有机酸**，具有**美白**和**促进代谢**功效"
        }
    ]

    # 各餐次的能量范围（单位：kcal）
    ENERGY_RANGES = {
        "早餐": (300, 500),    # 早餐能量范围
        "午餐": (500, 800),    # 午餐能量范围
        "晚餐": (400, 700)     # 晚餐能量范围
    }
    
    # 单个菜品的能量范围
    DISH_ENERGY_RANGES = {
        "主食": (150, 300),     # 米饭、面条等
        "蛋白质": (120, 250),   # 肉类、鱼类、豆制品
        "蔬菜": (30, 100),      # 各类蔬菜
        "汤品": (50, 150)       # 各类汤
    }

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
        
        if meal == "早餐":
            # 早餐搭配：主食 + 蛋白质 + 水果/蔬菜
            dishes.append(random.choice(cls.STAPLE_FOODS))
            dishes.append(random.choice(cls.PROTEIN_FOODS))
            if random.random() > 0.5:
                dishes.append(random.choice(cls.FRUIT_FOODS))
            else:
                dishes.append(random.choice(cls.VEGETABLE_FOODS))
                
        else:  # 午餐和晚餐
            # 主食
            dishes.append(random.choice(cls.STAPLE_FOODS))
            # 蛋白质（2个选择的概率）
            dishes.append(random.choice(cls.PROTEIN_FOODS))
            if random.random() > 0.7:
                dishes.append(random.choice(cls.PROTEIN_FOODS))
            # 蔬菜（必选）
            dishes.append(random.choice(cls.VEGETABLE_FOODS))
            # 汤品（80%概率）
            if random.random() > 0.2:
                dishes.append(random.choice(cls.SOUP_FOODS))
            # 水果（午餐50%概率）
            if meal == "午餐" and random.random() > 0.5:
                dishes.append(random.choice(cls.FRUIT_FOODS))
        
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
