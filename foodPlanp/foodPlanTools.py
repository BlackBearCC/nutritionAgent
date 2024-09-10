import os, json
import requests

import config.plan.diseasePrompt
from config.plan.diseasePrompt import *
from config.plan.promptConfig import *
from config.plan.CCprompt import *
"""
工具函数

- 首先要在 tools 中添加工具的描述信息
- 然后在 tools 中添加工具的具体实现

"""


def tools():
    tools = [{"type": "function",

              "function": {
                  'name': 'get_disease_prompt',
                  'description': '特定疾病饮食准则是获取某种疾病对应的饮食指南',
                  'parameters':
                      {
                          'type': 'object',
                          "properties": {
                              "query": {
                                  'description': '疾病名称',
                                  'type': 'string',
                              }

                          }, },
                  "required": ["query"],
              }, },
             {
                 "type": "function",
                 "function": {
                     'name': 'get_total_food_princeple',
                     'description': '饮食总原则是营养专家针对每一个普通人每天健康饮食要遵循的总原则',
                     'parameters': {"type": "object",
                                    "properties":
                                        {
                                            'query': {
                                                'description': '查询内容',
                                                'type': 'string',
                                            },
                                        },
                                    },
                     "required": ["query"],
                 },
             },
             {
                 "type": "function",
                 "function": {
                     'name': 'get_user_preference',
                     'description': '用户画像是获取每个用户的个性化信息',
                     'parameters': {"type": "object",
                                    "properties": {
                                        'query': {
                                            'description': '查询指令',
                                            'type': 'string',
                                        },
                                        'user_input': {
                                            'description': '用户输入,格式为dict',
                                            'type': 'string',
                                        }
                                    },
                                    },
                     "required": ["query", "user_input"],
                 },
             },

    {
        "type": "function",
        "function": {
            'name': 'get_CC_prompt',
            'description': '获取为了满足用户主诉应该遵循的膳食规则',
            'parameters': {"type": "object",
                           "properties":
                               {
                                   'query': {
                                       'description': '查询内容',
                                       'type': 'string',
                                   },
                           'user_input': {
                               'description': '用户输入,格式为dict',
                               'type': 'string',
                           }
                               },
                           },
            "required": ["query"],
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

def get_CC_prompt(query,user_input):
    user_CC = "无主诉"
    if "用户主诉" in query:
        if user_input["require"] in CCprompt.keys():
            user_CC=CCprompt[user_input["require"]]
    return user_CC


