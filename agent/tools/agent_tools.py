import json
import os
import random
import requests
from react_agent_customer_service.utils.config_handler import agent_conf
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from react_agent_customer_service.rag.rag_service import RagSummarizeService
from react_agent_customer_service.utils.path_tool import get_abs_path
from react_agent_customer_service.utils.logger_handler import logger
reg=RagSummarizeService()
user_ids=['1001','1002','1003','1004','1005','1006','1007','1008','1009','1010']
month_arr=['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06','2026-07',
           '2026-08','2026-09','2026-10','2026-11','2026-12']
external_data={}
@tool(description="从向量存储中检索参考资料")
def rag_summarize(query:str)->str:
    return reg.rag_summarize(query)

@tool(description='获取指定城市的实时天气，以消息字符串的形式返回')
def get_weather(city:str)->str:
    """通过 wttr.in 免费接口获取真实天气，失败时降级为默认描述。"""
    try:
        resp=requests.get(f'https://wttr.in/{city}',params={'format':'j1'},timeout=8,headers={'User-Agent':'curl'})
        resp.raise_for_status()
        data=resp.json()
        cur=data['current_condition'][0]
        desc=cur.get('weatherDesc',[{}])[0].get('value','未知')
        return (f'城市{city}当前天气：{desc}，气温{cur["temp_C"]}℃，体感{cur["FeelsLikeC"]}℃，'
                f'空气湿度{cur["humidity"]}%，风向{cur["winddir16Point"]}，风速{cur["windspeedKmph"]}km/h。')
    except Exception as e:
        logger.error(f'[get_weather]获取{city}天气失败：{str(e)}')
        return f'城市{city}天气为晴天，气温26摄氏度，空气湿度百分之五十，南风一级，AQI21，最近六小时降雨概率极低'

@tool(description='获取用户所在城市的名称，以纯字符串的形式返回')
def get_user_location(runtime:ToolRuntime)->str:
    city=runtime.context.get('city')
    if not city:
        city=random.choice(['深圳','杭州','合肥'])
    return city

@tool(description='获取用户的ID，以纯字符串形式返回')
def get_user_id(runtime:ToolRuntime)->str:
    user_id=runtime.context.get('user_id')
    if not user_id:
        user_id=random.choice(user_ids)
    return user_id

@tool(description='获取当前月份，以纯字符串形式返回')
def get_current_month(runtime:ToolRuntime)->str:
    month=runtime.context.get('month')
    if not month:
        month=random.choice(month_arr)
    return month

def generate_external_data():
    """
    'user_id:(
        'month':{'特征'：'xxxx','效率':'xxx'}
        'month':{'特征'：'xxxx','效率':'xxx'}
        'month':{'特征'：'xxxx','效率':'xxx'}
        ...
    )
    """
    if not external_data:
        external_data_path=get_abs_path(agent_conf['external_data_path'])
        if not os.path.exists(external_data_path):
            raise FileNotFoundError(f'外部数据文件{external_data_path}不存在')
        with open(external_data_path,'r',encoding='utf-8') as f:
            for line in f.readlines()[1:]:
                arr:list[str]=line.strip().split(",")
                user_id:str=arr[0]
                feature: str=arr[1]
                efficiency: str=arr[2]
                consumables: str=arr[3]
                comparison:str=arr[4]
                time:str=arr[5]

                if user_id not in external_data:
                    external_data[user_id]={}

                external_data[user_id][time]={
                    '特征':feature,
                    '效率':efficiency,
                    '耗材':consumables,
                    '对比':comparison,
                }

@tool(description='从外部系统中获取用户的使用记录，以纯字符串的形式返回，如果未检测到返回空字符串')
def fetch_external_data(user_id:str,month:str)->str:
    generate_external_data()

    try:
        record=external_data[user_id][month]
    except KeyError:
        logger.warning(f'[fetch_external_data]未能检索到用户id在这个月的检索记录')
        return ""
    return json.dumps(record,ensure_ascii=False)

@tool(description='无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息')
def fill_context_for_report():
    return 'fill_context_for_report已经调用'
