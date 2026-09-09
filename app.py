import time

import streamlit as st
from react_agent_customer_service.agent.react_agent import ReactAgent

#标题
st.title('智扫通机器人智能客服')
st.divider()

#侧边栏：模拟"当前登录用户"的运行时上下文，供工具通过 ToolRuntime 读取
with st.sidebar:
    st.subheader('用户详细信息')
    sel_user_id=st.selectbox('用户ID',['1001','1002','1003','1004','1005','1006','1007','1008','1009','1010'],index=0)
    sel_month=st.selectbox('月份',['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06',
                                   '2026-07','2026-08','2026-09','2026-10','2026-11','2026-12'],index=4)
    sel_city=st.selectbox('所在城市',['深圳','杭州','合肥'],index=1)
runtime_context={'user_id':sel_user_id,'month':sel_month,'city':sel_city}

if 'agent' not in st.session_state:
    st.session_state['agent'] = ReactAgent()
if 'message' not in st.session_state:
    st.session_state['message']=[]

for message in st.session_state['message']:
    st.chat_message(message['role']).write(message['content'])
#用户输入提示词
prompt=st.chat_input()

if prompt:
    st.chat_message('user').write(prompt)
    st.session_state['message'].append({'role':'user','content':prompt})

    response_messages=[]
    with st.spinner('智能客服思考中...'):
        res_stream=st.session_state['agent'].execute_stream(prompt,runtime_context=runtime_context)

        def capture(generator,cache_list):
            for chunk in generator:
                cache_list.append(chunk)

                for char in chunk:
                    time.sleep(0.01)
                    yield char


        st.chat_message('assistant').write_stream(capture(res_stream,response_messages))
        st.session_state['message'].append({'role':'assistant','content':response_messages[-1]})
        st.rerun()

