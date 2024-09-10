import random
import gradio as gr
from foodPlanp.foodPlan import *
from foodCheckp.foodCheck import *
foodPlan=foodPlanAgent()
foodCheck=foodCheckAgent()
history=[]

def chatAgent(message, userTag="无",reqire="无",history=None):
    count=0
    #conclu=True
    yield "方案正在生成中....\n","方案正在评估中....\n"
    user_input={}
    if history is None:
        history = []
    if len(message)<1:
        yield "输入不能为空"
    user_input["text"]=message
    user_input["userTag"]=userTag
    user_input["require"]=reqire
    user_input["history"]=[]
    print("input",user_input)
    if len(history)>0:
        for i in range(len(history)):
            if i%2==0:
                user_input["history"].append({"role":"user","content":history[i][0]})
            else:
                user_input["history"].append({"role":"assistant","content":history[i][0]})
    answer=""
    evares=""
    his=""
    evahis=[]
    user_input["history"].append({"role": "user", "content": user_input["text"]})
    history.append("USER: "+user_input["text"])
    res=foodPlan.get_recipe(user_input)
    for item in res:
        user_input["history"].append({"role": "assistant", "content": item})
        yield "", item
        answer+=item+"\n"
        eva=foodCheck.check_recipe(user_input,answer)
        for iter in eva:
            conclu=""
            print("iter:",iter)
            total_res=""
            evares=iter+"\n"
            if "True" in evares or "False" in evares:
                conclu=evares
            else:
                yield "", "\n\n" + evares
            if  "改善建议" in iter:
                total_res = iter.split("改善建议")[1]
            elif "调整" in iter:
                total_res = iter.split("调整")[1]
            elif "替换建议" in iter:
                total_res = iter.split("替换建议")[1]
            print("conclu",conclu)
            print(type(conclu))
            evahis.append(evares)
            while "False" in conclu and count<=1:
                user_input["history"].append({"role": "assistant", "content": total_res})
                count+=1
                answer=""
                print("history:",user_input["history"])
                res = foodPlan.get_recipe(user_input)
                for item in res:
                    print("item",item)
                    answer += item + "\n"
                    eva = foodCheck.check_recipe(user_input, answer)
                    for iter in eva:
                        print("iter",iter)
                        evares = iter + "\n"
                        if "True" in evares or "False" in evares:
                            conclu = evares
                        else:
                            yield "", "\n\n" + evares
                        # if "最终建议" in iter:
                        #     total_res=iter.split("最终结论")[1]
                        # elif "Final Answer" in iter:
                        #     total_res = iter.split("Final Answer")[1]
                        # elif "综合判定" in iter:
                        #     total_res = iter.split("综合判定")[1]
                        # elif "最终结论" in iter:
                        #     total_res = iter.split("最终结论")[1]
                        evahis.append(evares)
    print("count:",count)
    history.append("ASSISTANT: "+answer)
    print("history:",history)
    print("evahis:",evahis)
    yield history,""




# app=gr.ChatInterface(chatAgent,chatbot=gr.Chatbot(placeholder="<strong>##您口袋里的膳食营养家</strong><br>*更健康的一日三餐*",height=600),additional_inputs_accordion="用户信息",additional_inputs=[
#         gr.Textbox(label="请输入您的个人信息(如身高、体重、健康状况、年龄、性别等):",lines=2),gr.Textbox(label="请输入您的个人主诉:",lines=1)
#     ]).launch(share=True)

# port=8888
# app.root="/"+"AIAgent:"+str(port)
# app.share_url="http://lingtuoHealth.com"+app.root+"/"
#app.launch()



# 定义输出框
output1 = gr.Textbox(lines=26, scale=1, label="您的膳食方案专家")
output2 = gr.Textbox(lines=26, scale=1, label="您的膳食方案评估专家")

# 定义输入框
input1 = gr.Textbox(lines=1, placeholder="Input Here...",label="输入")
input2 = gr.Textbox(lines=1, placeholder="Disease Here...",label="健康信息")
input3 = gr.Textbox(lines=1, placeholder="Requirement Here...",label="主诉")

with gr.Blocks() as demo:
    with gr.Row():
        output1.render()
        output2.render()
    with gr.Row():
        submit_btn = gr.Button("submit")
        clear_btn = gr.Button("clear")
    with gr.Column():
        input1.render()
        input2.render()
        input3.render()


    def submit_callback(message, userTag="无", reqire="无", history=None):
        history_response1=""
        history_response2=""
        if history is None:
            history = []
        res = chatAgent(message, userTag,reqire,history)
        for content1, content2 in res:
            if isinstance(content1,list):
                history_response1="\n".join(item for item in content1)
            else:
                if len(content1)>1:
                    history_response1=content1
                else:
                    history_response1="方案正在生成中...."
            history_response2+=content2
            yield history_response1,history_response2

    submit_btn.click(submit_callback, inputs=[input1, input2, input3], outputs=[output1, output2])
    def clear_inputs():
        global history
        history = []
        return "", "", "","",""
    

    clear_btn.click(clear_inputs, inputs=[], outputs=[input1, input2, input3, output1, output2])

demo.launch(share=True)



