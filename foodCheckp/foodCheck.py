# -*- coding: utf-8 -*-
from openai import OpenAI
from config.check.totalConfig import *
from foodCheckp.planEvaluation import *
from foodCheckp.foodCheckLLM import *

client=OpenAI(api_key="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")
class foodCheckAgent:
    def __init__(self) -> None:
        self.model = Chat()
        self.tools=tools()
        self.system_prompt = self.build_system_input()
    def build_system_input(self):
        tool_descs, tool_names = [], []
        for tool in self.tools:
            tool_descs.append(tool["function"]['description'])
            tool_names.append(tool["function"]['name'])
        tool_descs = '\n\n'.join(tool_descs)
        tool_names = ','.join(tool_names)
        system_prompt=all.format(tool_descs=tool_descs, tool_names=tool_names)
        return system_prompt

    def check_recipe(self,user_input,response):
        mess=[]
        prompt=self.build_system_input().format(user_input)
        mess.append({"role":"system","content":prompt})
        mess.append({"role":"user","content":"""用户输入相关信息如下，你可以自主从下列内容获取你需要的信息，如体重，年龄。身高等："""+str(user_input)+"""请开始你的分析"""})
        #print(mess)
        tools=self.tools
        print("check result:",self.check_is_recipe(response))
        if bool(self.check_is_recipe(response))==True:
            for item in  self.model.get_answer(mess,tools,user_input,response):
                yield item

    def check_is_recipe(self,response):
        mess=[]
        mess.append({"role": "user",
                     "content": """你是一个内容处理专家，你需要判断下列输入是否包含菜谱、食材清单、饮食列表，如果是，请返回True，否则返回False。""" + str(
                         response) + """请输出你的答案"""})
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=mess,
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            max_tokens=1256,
            stream=False
        )
        return response.choices[0].message.content


response="""
日饮食清单
早餐
燕麦粥（50克，碳水化合物，有助于尿酸排出）
鸡蛋（50克，低脂肪，适量蛋白质）
苹果（1个，富含维生素）
午餐
糙米饭（150克，富含纤维，有助于尿酸排出）
蒸鸡胸肉（100克，低嘌呤，低脂高蛋白）
青菜（200克，富含维生素和纤维）
晚餐
全麦面包（50克，低嘌呤，碳水化合物促进尿酸排出）
煮红萝卜（150克，嘌呤指数低，有助于尿酸控制）
黄瓜（100克，富含维生素和水分）
零食
无糖酸奶（100ml，低脂肪，有少量蛋白质）
坚果（30克，避免过量脂肪摄入）
根据尿酸高的饮食准则，这份饮食计划力求减少嘌呤摄入，同时保证了食物种类多样，以满足您每日的营养需求。希望对您有帮助！"""

# user_input={'text': '明天吃什么', 'userTag': '疾病：尿酸高\n身高：175厘米\n体重：80公斤\n年龄：30岁\n性别：男', 'require': '降尿酸', 'history': []}
# ag=foodCheckAgent()
# res=ag.check_recipe(user_input,response)
# for a in res:
#     print(a)