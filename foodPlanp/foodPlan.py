# -*- coding: utf-8 -*-
from openai import OpenAI
from config.plan.promptConfig import *
from foodPlanp.foodPlanTools import *
from foodPlanp.foodPlanLLM import *

# from foodPlanTools import *
# from foodPlanLLM import Chat

client=OpenAI(api_key="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")




class foodPlanAgent:
    def __init__(self) -> None:
        self.model = Chat()
        self.tools=tools()
    def build_system_input(self,user_input):
        tool_descs, tool_names = [], []
        for tool in self.tools:
            tool_descs.append(tool["function"]['description'])
            tool_names.append(tool["function"]['name'])
        tool_descs = '\n\n'.join(tool_descs)
        tool_names = ','.join(tool_names)
        system_prompt=prompt["system_prompt"].format(user_input=user_input,tool_descs=tool_descs, tool_names=tool_names)
        return system_prompt

    def get_recipe(self,user_input):

        mess=[]
        prompt=self.build_system_input(user_input)
        mess.append({"role":"system","content":prompt})
        tools=self.tools
        if len(user_input["history"])>0:
            for item in user_input["history"]:
                mess.append(item)
        mess.append({"role":"user","content":"如果已经在上下文中告知了风险食物名称和有问题的食材，在重新生成食谱时你会很好的替换这些食物"})
        print("mess:",mess)
        for item in self.model.get_answer(mess,tools,user_input):
            #print(item)
            yield item



# model=foodPlanAgent()
# input1={'text': '给我制定一个明日饮食方案', 'userTag': '疾病：尿酸高\n身高：175厘米\n体重：80公斤\n年龄：30岁\n性别：男', 'require': '美白', 'history': []}
# res=model.get_recipe(input1)
# for a in res:
#     print(a)

#{"role":"assistant","content":"""最终获取到的信息如下：
# ### 饮食总准则：
# 1. 食物多样，合理搭配：每天的膳食应包括谷薯类、蔬菜水果、畜禽鱼蛋奶和豆类食物。平均每天摄入12种以上食物，每周25种以上，合理搭配。每天摄入谷类食物200~300g（其中包含全谷物和杂豆类50~150g；薯类50~100g）。餐餐有蔬菜，保证每天摄入不少于300g的新鲜蔬菜，深色蔬菜应占1/2。天天吃水果，保证每天摄入200~350g的新鲜水果，果汁不能代替鲜果。吃各种各样的奶制品，摄入量相当于每天300ml以上液态奶。鱼、禽、蛋类和瘦肉摄入要适量，平均每天120~200g。此外，每周最好吃鱼2次或300~500g，蛋类300~350g，畜禽肉300~500g。
# 用户画像：
# - 疾病：高血压
# - 饮食偏好：爱吃肉
# 高血压的饮食准则：
# 1. 每日摄入脂肪不超过50克。
# 2. 应食用每100克含胆固醇少于200毫克的食物。
# 3. 每日摄入胆固醇含量应小于300毫克。
# 4. 青菜每天不得少于500克。
# 5. 要吃低盐，高钾，高纤维的饮食。
# 用户主诉：
# - 希望美白皮肤
# 1. 多食用富含维生素C的食品，如柑橘类水果、草莓、蔬菜等。每日维生素C摄入量不少于100毫克。
# 2. 多食用富含胶原蛋白的食品，如鱼类、肉类、豆类等。
# 3. 多食用富含抗氧化剂的食品，如坚果、谷物、水果等。
# 4. 多食用富含不饱和脂肪酸的食品，如鱼类、坚果、橄榄油等。
# 5. 避免食用过多的含糖饮料和食品，如糖果、甜点、碳酸饮料等。
# 综合建议：
# 在优先满足高血压饮食准则的前提下，满足饮食总准则，并结合用户的饮食偏好和主诉，推荐以下每日食材：
# 早餐：
# - 燕麦片：50克（低盐、高纤维食物，有助于血压控制）
# - 鸡蛋：50克（富含胶原蛋白）
# - 牛奶：200毫升（适量奶制品）
# - 橙子：100克（富含维生素C，满足美白需求）
# 午餐：
# - 糙米饭：150克（富含纤维，有助于血压控制）
# - 鸡胸肉：100克（低脂、高蛋白，满足饮食偏好）
# - 西兰花：200克（富含维生素C和纤维）
# - 胡萝卜：100克（富含维生素C）
# 晚餐：
# - 全麦面包：50克（低盐、高纤维）
# - 三文鱼：100克（富含不饱和脂肪酸，满足饮食偏好）
# - 菠菜：200克（高纤维、高钾，有助于血压控制）
# - 番茄：100克（富含维生素C）
# 零食：
# - 坚果：30克（富含抗氧化剂和不饱和脂肪酸）
# - 草莓：100克（富含维生素C）
# 注：
# - 以上食材中橙子、西兰花、胡萝卜、番茄和草莓对高血压有改善作用。
# - 鸡胸肉和三文鱼富含胶原蛋白和不饱和脂肪酸，能满足您的饮食偏好，并有助于血压控制。
# - 燕麦片、全麦面包、糙米饭、坚果、牛奶、橙子、草莓和其他蔬菜水果富含维生素C，有助于满足您的美白需求。"""}]})
# print(res)
#
# user_input={'text': '今天在医院查到尿酸偏高，想要通过饮食调理把尿酸降下去，给我输出一个饮食方案。', 'userTag': '疾病：尿酸高\n身高：175厘米\n体重：80公斤\n年龄：30岁\n性别：男', 'history': []}
# get_CC_prompt("",user_input)