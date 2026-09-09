from langchain.agents import create_agent
from react_agent_customer_service.model.factory import chat_model
from react_agent_customer_service.utils.prompt_loader import load_system_prompts
from react_agent_customer_service.agent.tools.agent_tools import (rag_summarize,get_weather,get_user_location,get_user_id,get_current_month,
                                               fetch_external_data,fill_context_for_report)
from react_agent_customer_service.agent.tools.middleware import monitor_tool,log_before_model,report_prompt_switch


class ReactAgent:
    def __init__(self):
        self.agent=create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[rag_summarize,get_weather,get_user_location,get_user_id,get_current_month,
                                               fetch_external_data,fill_context_for_report],
            middleware=[monitor_tool,log_before_model,report_prompt_switch]
        )
    def execute_stream(self,query:str,runtime_context:dict=None):
       input_dict={
            'messages':[
                {'role':'user','content':query},
            ]
       }
       #第三个参数context就是我们的上下文runtime中的信息，就是我们做提示词切换的标记
       #runtime_context用于把前端（如Streamlit侧边栏）选择的user_id/month/city注入工具运行时
       context={'report':False}
       if runtime_context:
            context.update(runtime_context)
       for chunk in self.agent.stream(input_dict,stream_mode='values',context=context):
           latest_message=chunk['messages'][-1]
           if latest_message.content:
                yield latest_message.content.strip() + '\n'
