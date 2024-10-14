from openai import OpenAI
import logging
import time
from termcolor import colored
from foodCheckp.planEvaluation import *

client=OpenAI(api_key="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")


class Chat:
    def __init__(self):
        self.keys = "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"
        self.count = 0

    def manageMultiKeys(self,count):
        api_keys=["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","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"]
        if count%2==0:
            self.keys=api_keys[0]
        else:
            self.keys=api_keys[1]
        return self.keys

    def get_answer(self,mess,tools,user_input,res):
        second_response=""
        recipe={}
        index_json={}
        a=time.time()
        temp=""
        response = client.chat.completions.create(
                model="gpt-4o",
                messages=mess,
                tools=tools,
                temperature=0,
                top_p=1,
                frequency_penalty=0,
                max_tokens=1256,
                stream=False
            )
        ans = response.choices[0].message
        tool_calls = ans.tool_calls
        mess.append(ans)
        while tool_calls:
            available_functions = {
                    "check_recipe_disease": check_recipe_disease,
                    "check_recipe_erengy": check_recipe_erengy,
                    "check_recipe_user_CC":check_recipe_user_CC,
                    "tranform_recipe_2_json":tranform_recipe_2_json,
                    "get_food_index":get_food_index}

            #print("mess1",mess)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                #print("function_name",function_name)
                function_to_call = available_functions[function_name]
                #print("function_to_call",function_to_call)
                function_args = json.loads(tool_call.function.arguments)
                #print("function_args",type(function_args),function_args)
                if function_name == 'tranform_recipe_2_json':
                    recipe = function_to_call(recipe=res)
                    #print(recipe)
                    mess.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": str(recipe)
                        })
                elif function_name=="get_food_index":
                    index_json=function_to_call(recipe_json=recipe,user_input=user_input)
                    mess.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": str(index_json)
                        })
                    for key,item in index_json[1].items():
                        temp+=str(key)+":"+str(item)+"\n"
                    yield """\n查询食材库，获得每100克食材的营养含量:\n"""+temp
                elif function_name == 'check_recipe_user_CC' or function_name == 'check_recipe_erengy':
                    user_input = user_input
                    result = function_to_call(user_input=user_input, recipe_json=recipe,index_json=index_json)
                    #print("res",result)
                    mess.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": result
                        })
                    yield result
                else:
                    query = function_args.get("query")
                    result = function_to_call(query=query,recipe_json=recipe,index_json=index_json)
                    #print("res", result)
                    mess.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": result
                        })
                    yield result
            #print("mess:", mess)
            second_response = client.chat.completions.create(
                model="gpt-4o",
                messages=mess,
                tools=tools
                )
            b = time.time()
            #print(b - a)
            tool_calls=second_response.choices[0].message.tool_calls
            #print("second",tool_calls)
            if tool_calls:
                mess.append(second_response.choices[0].message)
            else:
                yield second_response.choices[0].message.content
                print("text:",second_response.choices[0].message.content)
                yield self.res_reflection(second_response.choices[0].message.content)



    def res_reflection(self, res):
        mess = [{"role": "system",
                     "content": """你是一个语言理解专家，你能准确的理解文本中对食谱方案的结论是通过还是不通过，只要满足所有重要原则的时候就通过，不考虑建议规则是否满足。如果通过返回True,否则返回False,只输出这两个单词不要输出其他文字"""},
                    {"role": "user", "content": f"专家意见：{res}\n"}]
        response = client.chat.completions.create(
                model="gpt-4o",
                messages=mess,
                temperature=0,
                top_p=1,
                frequency_penalty=0,
                max_tokens=256,
                stream=False
            )
        return response.choices[0].message.content