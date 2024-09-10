# -*- coding: utf-8 -*-
from openai import OpenAI
import logging
import time
from termcolor import colored

import foodPlanp.foodPlanTools
from foodPlanp.foodPlanTools import *
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

    def get_answer(self,mess,tools,user_input):
        if len(user_input["history"])>0:
            for item in user_input["history"]:
                mess.append(item)
        query = user_input["text"]
        mess.append({"role":"user","content":query})
        second_response=""
        #print("1")
        try:
            a=time.time()
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
            print("ans",ans)
            tool_calls = ans.tool_calls
            if ans.content is not None and "是" in self.res_reflection(mess,ans.content,user_input) and tool_calls is None:
                yield ans.content
            else:
                self.get_answer(mess, tools, user_input)
            tool_calls = ans.tool_calls
            mess.append(ans)
            while tool_calls:
                available_functions = {
                    "get_disease_prompt": get_disease_prompt,
                    "get_total_food_princeple": get_total_food_princeple,
                    "get_user_preference": get_user_preference,
                    "get_CC_prompt":get_CC_prompt}

                #print("mess1",mess)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    #print(function_name)
                    function_to_call = available_functions[function_name]
                    #print(function_to_call)
                    function_args = json.loads(tool_call.function.arguments)
                    #print(function_args)
                    query = function_args.get("query")
                    if function_name == 'get_user_preference' or function_name == 'get_CC_prompt':
                        user_input = user_input
                        result = function_to_call(query, user_input)
                        #print("res",result)
                        mess.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": result
                        })
                    else:
                        result = function_to_call(query=query)
                        #print("res",result)
                        mess.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": result
                        })
                #print("mess:", mess)
                second_response = client.chat.completions.create(
                model="gpt-4o",
                messages=mess,
                tools=tools
                )
                print("second_res",second_response.choices[0].message)

                b = time.time()
                tool_calls=second_response.choices[0].message.tool_calls
                #print("second tools:",tool_calls)
                if tool_calls:
                    mess.append(second_response.choices[0].message)
                    # if second_response.choices[0].message.content is not None:
                    #     yield second_response.choices[0].message.content
                else:
                    if "是" in self.res_reflection(mess, second_response.choices[0].message.content,user_input):
                        yield second_response.choices[0].message.content

                    else:
                        self.get_answer(mess, tools, user_input)
        except Exception as e:
            #print(e)
            logging.info("error:{}".format(e))
            self.count += 1
            self.manageMultiKeys(self.count)
            print("except mess",mess)
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
            #print("ans:",ans)
            tool_calls = ans.tool_calls
            while tool_calls:
                available_functions = {
                    "get_disease_prompt": get_disease_prompt,
                    "get_total_food_princeple": get_total_food_princeple,
                    "get_user_preference": get_user_preference}
                mess.append(ans)
                #print("mess1", mess)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = available_functions[function_name]
                    function_args = json.loads(tool_call.function.arguments)
                    query = function_args.get("query")
                    if function_name == 'get_user_preference':
                        user_input = user_input
                        result = function_to_call(query, user_input)
                        mess.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": result
                        })
                    else:
                        result = function_to_call(query=query)
                        mess.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": result
                        })
                second_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=mess,
                    tools=tools
                )
                b = time.time()

                tool_calls = second_response.choices[0].message.tool_calls
                if tool_calls:
                    mess.append(second_response.choices[0].message)
                else:
                    if "是" in self.res_reflection(user_input, second_response.choices[0].message.content,user_input):
                        return second_response.choices[0].message.content
                    else:
                        self.get_answer(mess,tools,user_input)


    # def tool_calls(self):


    def pretty_print_conversation(self,messages):
        role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "function": "magenta",
        }

        for message in messages:
            if message["role"] == "system":
                print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "user":
                print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "assistant" and message.get("function_call"):
                print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
            elif message["role"] == "assistant" and not message.get("function_call"):
                print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
            elif message["role"] == "function":
                print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))

    def res_reflection(self,mess,res,user_input):
        if len(mess)>1:
            mess=[{"role":"system","content":"""你是一个问答评估专家，你能准确的评估出答案内容是否和问题匹配，不要管是否简洁。如果用户问吃什么或者饮食方案之类的问题，我们需要给出食材清单、食材列表或者食谱，如果给出了食材清单、食材列表或者食谱，则回答“是”，否则回答“否”；你需要从用户输入信息中判断用户是否提供了疾病，主诉等信息，用户输入信息如下"""+str(user_input)+"""如果用户提供的信息不够，答案内容是对用户信息的反问则回答”是“，如果是其他问题则直接回答问题。如果能解决用户最终的问题则回答"是"，否则回答"否"""},{"role":"user","content":f"问题及历史信息：{mess}\n答案内容：{res}"}]
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




