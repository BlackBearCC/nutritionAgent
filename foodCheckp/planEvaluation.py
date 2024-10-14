# -*- coding: utf-8 -*-
import os, json
import requests

import config.plan.diseasePrompt
from config.plan.diseasePrompt import *
from config.plan.promptConfig import *
from config.plan.CCprompt import *
from config.check.indexMap import index,unit
from openai import OpenAI
import pymysql
from volcenginesdkarkruntime import Ark

client=OpenAI(api_key="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")
client1 = Ark(ak="AKLTZWM2MjE2MDdjMmMxNDIyYThkNjdkZTVkNTFmMTYyNWI", sk="TldJNVlXSmlNbVV3TTJSbU5ERXhaV0psTURJNU1HUXpPR1E0TlRnNFl6RQ==",api_key="4d57d68c-5355-404a-8ff5-776113cfdd0f")

conn = pymysql.connect(
        host='172.16.10.129',
        user='root',
        password='oldhan',
        db='lingtuo-ai',
        port=3306
    )
cur = conn.cursor()
"""
工具函数

- 首先要在 tools 中添加工具的描述信息
- 然后在 tools 中添加工具的具体实现

"""
def tools():
    tools = [{"type": "function",

              "function": {
                  'name': 'check_recipe_disease',
                  'description': '验证食材清单是否符合特定疾病饮食准则工具',
                  'parameters':
                      {
                          'type': 'object',
                          "properties": {
                              "query": {
                                  'description': '疾病名称',
                                  'type': 'string',
                              }

                          },
                          "recipe_json": {
                              'description': 'json格式的食材清单',
                              'type': 'string',
                          },
                          "index_json":{"description":"json格式的每种食物单位重量里的营养成分含量",
                                        "type":"string"}
                      },
                  "required": ["query","recipe_json","index_json"],
              }, },
             {
                 "type": "function",
                 "function": {
                     'name': 'check_recipe_erengy',
                     'description': '对食材清单是否符合饮食总原则进行评估验证的工具',
                     'parameters': {"type": "object",
                                    "properties":
                                        {'user_input':{"description":"用户输入信息",
                                                          "type":"string"},
                                        'recipe_json': {
                                                'description': '包含食材清单的json数据',
                                                'type': 'string',
                                            },
                                        'index_json':{
                                            'description': 'json格式的每种食物单位重量里的营养成分含量',
                                            'type': 'string',
                                        }
                                        },
                                    },
                     "required": ["user_input","recipe_json","index_json"],
                 },
             },

    {
        "type": "function",
        "function": {
            'name': 'check_recipe_user_CC',
            'description': '获取为了满足用户主诉应该遵循的膳食规则的工具',
            'parameters': {"type": "object",
                           "properties":
                               {
                                   'user_input': {
                                       'description': '用户输入,格式为json',
                                       'type': 'string',
                                   },
                           'recipe_json': {
                               'description': '包含食材清单的json数据',
                               'type': 'string',
                           },
                           'index_json': {
                                       'description': 'json格式的每种食物单位重量里的营养成分含量',
                                       'type': 'string',
                                   }
                               },
                           },
            "required": ["user_input","recipe_json","index_json"],
        },
    },
             {
                 "type": "function",
                 "function": {
                     'name': 'tranform_recipe_2_json',
                     'description': '将文本格式的食材转化为json格式',
                     'parameters': {"type": "object",
                                    "properties":
                                        {
                                            'recipe': {
                                                'description': '包含食材的文本',
                                                'type': 'string',
                                            },
                                        },
                                    },
                     "required": ["recipe"],
                 },
             },
             {
                 "type": "function",
                 "function": {
                     'name': 'get_food_index',
                     'description': '获取食物单位重量里营养成分的含量',
                     'parameters': {"type": "object",
                                    "properties":
                                        {
                                            'recipe_json,': {
                                                'description': '包含食材的json数据',
                                                'type': 'string',
                                            },

                                              'user_input':{
                                                  'description': '用户输入',
                                                  'type': 'string',
                                              }

                                        },
                                    },
                     "required": ["recipe_json","user_input"],
                 },
             }
             ]
    return tools

def get_disease_prompt(query:str):
    """
    获取疾病对应的饮食指南
    :param query:疾病名称
    :return:疾病对应的饮食指南
    """
    disease_prompt="无"
    if query in config.plan.diseasePrompt.disease_prompt.keys():
        disease_prompt=config.plan.diseasePrompt.disease_prompt[query]
    return disease_prompt

def get_total_food_princeple(query:str):
    food_total_princeple=""
    if query=="饮食总则" or query=="饮食总准则":
        food_total_princeple=prompt["food_total_princeple"]
    return food_total_princeple

def get_user_preference(query:str,user_input):
    user_preference="无"
    if query=="用户画像":
        user_preference=user_input["userTag"]
    return user_preference

def get_CC_prompt(user_input):
    user_CC = "无主诉"
    if user_input["require"] in CCprompt.keys():
        user_CC=CCprompt[user_input["require"]]
    return user_CC

# def recipe_extract(response):
#     mess = [{"role": "system",
#              "content": """你是文本处理专家，你能准确的从文本中找出食物清单的文本块，并输出，其他不做任何处理。文本内容如下：""" + response + """请直接输出文本，不要输出思考过程,直接输出text文本""" }
#             ]
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=mess,
#         temperature=0,
#         top_p=1,
#         frequency_penalty=0,
#         max_tokens=1256,
#         stream=False
#     )
#     return response.choices[0].message.content


def tranform_recipe_2_json(recipe):
    """将食谱里的食材转化成一个json格式 {”食材名称“：”克重“}"""
    mess = [{"role": "system",
             "content": """你是一个数据处理专家，你能准确的从文本中找出食材名称（切记是食材而不是食谱），并提取对应的克重，以{"食材名称"："克重"}格式返回,输入食谱示例如下：水煮鸡蛋 50克，低脂牛奶 200毫升，橙子 100克，清蒸鸡胸肉 100克。输出示例如下：{"鸡蛋":"50克","牛奶":"200毫升","橙子":"100克","鸡胸肉":"100克"}，严格按照示例格式输出。不要添加其他描述内容，不要在开头输出```json这个字符串，只输出标准的json结构。食谱内容如下：""" + recipe }
            ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=mess,
        temperature=0,
        top_p=1,
        frequency_penalty=0,








































































































        ....................................................................

































































        
        max_tokens=1256,
        stream=False
    )
    return response.choices[0].message.content

def complete_data(foodName,indexName,unitName):
    mess = [
        {"role": "system", "content": "你是一个高级营养师，你知道所有食材的营养成分含量，现在请提供每100克"+foodName+"所包含的"+indexName+"是多少"+unitName+"在数据后标注（搜索补全）。注意，你提供的数据将用于病人的配餐指导，务必提供真实数据，不得编造。以下是举例：如输入：苹果所包含的维生素C是多少毫克，输出：4毫克（搜索补全）。只需输出所问的答案即可，不需额外的信息"},
        {"role": "user", "content": "请严格按照例子输出格式完成上述任务，只需输出数据和单位，不需要输出食物名称及营养成分含量"},]
    try:
        completion = client1.chat.completions.create(
            model="ep-20240715065903-4bx87",
            messages=mess,
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        print("doubao model error",e)
        answer="未知"

    return answer

def get_food_index(recipe_json,user_input):
    key_index=["能量"]
    mess = [{"role": "system",
             "content": """你是一个信息处理专家，你能准确的从输入信息中找出用户的疾病和健康诉求信息，以列表形式返回，举个例子：输入信息：{'text': '给我制定一个明日饮食方案', 'userTag': '疾病：尿酸高\n身高：175厘米\n体重：80公斤\n年龄：30岁\n性别：男', 'require': '美白', 'history': []}。输出信息：["尿酸高","美白"]。信息如下：""" + str(user_input)}
            ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=mess,
        temperature=0,
        top_p=1,
        frequency_penalty=0,
        max_tokens=1256,
        stream=False
    )
    result=response.choices[0].message.content
    for item in eval(result):
        if item in index.keys() and index[item] not in key_index:
            key_index.append(index[item])
    col=",".join(key_index)
    index_json={}
    for item in eval(recipe_json):
        index_json[item] = {}
        sql="SELECT "+col+" FROM food_ingredient WHERE 食材名称='"+item+"' or 食材通俗名称='"+item+"'"
        cur.execute(sql)
        results = cur.fetchall()
        if len(results)>0:
            for i in range(len(results[0])):
                if results[0][i]==-100:
                    index_json[item][key_index[i]]=complete_data(item,key_index[i],unit[key_index[i]])
                else:
                    index_json[item][key_index[i]]=str(results[0][i])+unit[key_index[i]]
                    #print(index_json)
        else:
            for i in range(len(key_index)):
                index_json[item][key_index[i]]=complete_data(item,key_index[i],unit[key_index[i]])

    return recipe_json,index_json


def check_recipe_erengy(user_input,recipe_json,index_json):
    total_princeple=get_total_food_princeple("饮食总准则")

    mess = [{"role": "system",
             "content": """你是一个数学家，你能准确的从json数据中确定食物类别和每种食材在100克时所包含指定成分的含量，并计算食谱中食材类别的总克重是否在饮食总原则中规定的范围（同时，你也了解每种食材的类别，比如西兰花、胡萝卜、西红柿都是深色蔬菜），也能准确的根据食物克重和单位重量的指标含量计算出每个指标的累计含量。如果满足所有的饮食总原则的要求，则通过该食谱方案。若满足重要规则，部分建议规则不满足，则给出改善建议，通过该食谱方案。若不满足重要建议，则该饮食方案评审不通过。饮食总原则内容如下："""+total_princeple+"""给用户的食材清单及克重包含在下json中，其中json的key为食材名称，值为食材克重："""+str(recipe_json)+"""，每种食材100克中包含能量数据在下列json中"""+str(index_json)+"""你需要根据每种食材每100克所含能量数据和食材重量计算出食材所包含的能量，在计算出所有食材的能量和人体每日能量上限进行比较，以判断食谱是否满足饮食总原则的重要规则。然后再计算每类食材重量判断是否满足建议规则，用户信息如下："""+str(user_input)},
            {"role": "user",
             "content": "1、为保证用户易读性，公式中的符号务必用通用数学符号如：+-*/，不要出现英文单词。2、最终结论说明通过或不通过，满足重要规则则通过，不满足重要规则则不通过，不通过的情况需要列出风险食物和对应的替换食物。3、所有的答案必须用中文，在答案最开头输出验证的目标名称，如：饮食总原则验证如下："}
            ]
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

def check_recipe_disease(query,recipe_json,index_json):
    disease_prompt=get_disease_prompt(query)
    mess = [{"role": "system",
             "content": """你是一个数学家和信息处理专家，你需要验证所给食材是否满足用户疾病饮食指南。用户疾病对应的饮食指南内容如下："""+str(disease_prompt)+"""给用户的食材清单包含在下列json数据中，"""+str(recipe_json)+"""每种食材所包含的营养成分(每100克包含营养成分的含量)含量在下列json数据中"""+str(index_json)+"""你需要先判断食材类别，再将他们划分到疾病对应的饮食指南的类别中，然后分析每个类别的配比，最后判断整个清单是否合格,也能准确的根据食物克重和单位重量的指标含量计算出每个指标的累计含量，判断食谱是否满足疾病饮食原则的重要规则。然后再计算每类食材重量判断是否满足建议规则.你的答案需要首先输出评估的依据再你的评估分析过程和最终结论"""},
            {"role":"user","content":"1、为保证用户易读性，公式中的符号用通用数学符号如：+-*/。2、最终结论只说明通过或不通过，满足重要规则则通过，不满足重要规则则不通过，不通过的情况需要列出风险食物和对应的替换食物。3、不要输出食材清单及营养成分，直接输出分析计算过程及结论，如果不通过会找出最有风险的食物。4、所有的答案必须用中文，在答案最开头输出验证的目标名称，如：用户疾病饮食原则验证如下："}]

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

# def check_recipe_user_preference(query,user_input,recipe):
#     userTag=get_user_preference(query,user_input)
#     mess = [{"role": "system",
#              "content": """你是一个美食家，你很了解每种食材的风味和口感，你只会根据给出的用户画像归纳出用户的口味偏好，然后根据食材清单判断每种食材的味道和口感（不会判断用户健康状况与食材的关系），是否符合用户的口味和食材种类偏好，如果没有获得饮食偏好信息，默认所有食材符合用户偏好。
#              用户画像内容如下："""+userTag+"""你会根据用户画像抽取用户饮食喜好，判断食材是否满足用户喜好。给用户的食材清单包含在下列文本中"""+recipe+"""
#              记住你只是一个美食家，只了解美食的口味和食材种类的特点，不会理解食材与用户健康的关系，不会判断食材与用户的健康状况的关系。你会对整个食材进行分析，不会一一罗列每个食材的味道和口感，只会判断食材是否满足用户的口味偏好。
#              只输出结论
#              示例1：
#              用户画像：45岁中年人，患有糖尿病，爱吃辣，食材清单是：番茄，鱼，辣椒。
#              思考：用户喜欢吃辣，食材清单里有辣椒，符合用户口味偏好
#              结论：您是一个喜欢吃辣的人，而食材里面包含辣椒，所以这个食材符合您的饮食偏好。
#              示例2：
#              用户画像：用户不爱吃芹菜，食材清单是：芹菜，鱼，辣椒。
#              思考：用户不爱吃芹菜，食材里面包含芹菜，所以这个食材不符合用户的要求。
#              结论：用户不爱吃芹菜，而食材里面包含芹菜，所以这个食材清单不符合用户的饮食偏好，应该将芹菜换成其他蔬菜。
#              """}]
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=mess,
#         temperature=0,
#         top_p=1,
#         frequency_penalty=0,
#         max_tokens=1256,
#         stream=False
#     )
#     return response.choices[0].message.content

def check_recipe_user_CC(user_input,recipe_json,index_json):
    user_CC=get_CC_prompt(user_input)
    mess = [{"role": "system",
             "content": """你是一个数学家和信息处理专家，你需要验证食材清单是否满足用户主诉对应的饮食指南。用户主诉对应的饮食指南内容如下："""+user_CC+"""给用户的食材清单包含在下列json数据中，"""+str(recipe_json)+"""每种食材所包含的营养成分(每100克包含营养成分的含量)含量在下列json数据中"""+str(index_json)+"""你需要先判断食材类别，再将他们划分到主诉对应的饮食指南的类别中，然后分析每个类别的配比，最后判断整个清单是否合格,也能准确的根据食物克重和单位重量的指标含量计算出每个指标的累计含量，判断食谱是否满足主诉的重要规则。然后再计算每类食材重量判断是否满足建议规则.你的答案需要首先输出评估的依据再你的评估分析过程和最终结论"""},
            {"role":"user","content":"1、为保证用户易读性，公式中的符号用通用数学符号如：+-*/。2、最终结论只说明通过或不通过，满足重要规则则通过，不满足重要规则则不通过，不通过的情况需要列出风险食物和对应的替换食物。3、不要输出食材清单及营养成分，直接输出分析计算过程及结论。4、所有的答案必须用中文，在答案最开头输出验证的目标名称，如：用户主诉饮食原则验证如下："}]
    #print(mess)
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


recipe="""
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
"""

# user_input={'text': '明天吃什么', 'userTag': '疾病：尿酸高\n身高：175厘米\n体重：80公斤\n年龄：30岁\n性别：男', 'require': '降尿酸', 'history': []}
# #print(check_recipe_user_preference("用户画像",user_input,recipe))
# print(tranform_recipe_2_json(recipe))
# recipe_json={"鸡蛋":"50克","牛奶":"200毫升","橙子":"100克","鸡胸肉":"100克"}
# user_input={'text': '明天吃什么', 'userTag': '疾病：尿酸高\n身高：175厘米\n体重：80公斤\n年龄：30岁\n性别：男', 'require': '降尿酸', 'history': []}
# res1,res2=get_food_index(recipe_json,user_input)
# res3=check_recipe_user_CC(user_input,res1,res2)
# print(res3)
