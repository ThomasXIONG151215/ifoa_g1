import streamlit as st

import json

from langchain_community.llms import Tongyi
from langchain_community.llms.moonshot import Moonshot
from langchain_experimental.agents import create_pandas_dataframe_agent
import boto3
import matplotlib.pyplot as plt 
import cv2

#st.set_page_config(page_title='室墨司源', layout='wide')

# AWS and S3 configuration
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
AWS_DEFAULT_REGION = st.secrets["AWS_DEFAULT_REGION"]
S3_BUCKET_NAME = "ifoag1"

s3_client = boto3.client('s3', 
                         aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                         region_name=AWS_DEFAULT_REGION)

# LLM configuration
langchain_llm = Tongyi(temperature=0,
                       api_key="sk-a36dbf13c32f4b28a7dfc3ba81275fa8",
                       base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

moonshot_llm = Moonshot(model="moonshot-v1-128k",
                        api_key="sk-wQJ6rfZixFKs8eKyPmAzXBfS1qdObnPbCIEoMyr6nq3i4IMd")

# Data loading functions

def load_data(conn):
    try:
        return conn.read("ifoag1/integral_data2.csv", input_format="csv", ttl=600)
    except Exception as e:
        st.error(f"从S3加载数据时出错: {str(e)}")
        return None

def load_settings(conn):
    try:
        return conn.read("ifoag1/settings.json", input_format="json", ttl=600)
    except Exception as e:
        st.error(f"从S3加载设置时出错: {str(e)}")
        return None

def save_settings(conn, settings):
    try:
        conn.write("settings.json", json.dumps(settings, indent=2))
        st.success("设置更新成功!")
    except Exception as e:
        st.error(f"更新设置失败: {str(e)}")



#@st.cache_data 
def data_analysis(agent_data_analyst):
    questions = [
        "**这里是否缺失数据?**",
        "**当前室内温度和湿度稳定性如何？**",
        "**当前CO2浓度变化规律如何**",
    ]
    
    avatar = ':material/cruelty_free:'
    combined_info = ""
    
    for question in questions:
        st.write(question)
        message = st.chat_message(name="ai", avatar=avatar)
        answer = agent_data_analyst.run("请用中文回答: " + question)
        message.write(answer)
        combined_info += question + "\n" + answer + "\n\n"
    
    # 生成总结报告
    summary_prompt = "基于以下分析结果,请生成一个简洁的总结报告,突出关键发现和建议:\n\n" + combined_info
    summary = agent_data_analyst.run(summary_prompt)
    
    st.write("**总结报告**")
    message = st.chat_message(name="ai", avatar=':material/file-document-outline:')
    message.write(summary)
    
    
    return combined_info, summary


@st.cache_resource
def manual_chat(agent_data_analyst,prompt):
    my_data_problem = agent_data_analyst.run(prompt)
    avatar = ':material/cruelty_free:'
    message = st.chat_message(name="ai",
                            avatar=avatar
                            )
    return message, my_data_problem

def ai_assistants(df):
    agent_data_analyst = create_pandas_dataframe_agent(moonshot_llm#langchain_llm
                                                       , 
                                                       df, verbose=True, allow_dangerous_code=True)
    data_analysis(agent_data_analyst)
    
    prompt = st.chat_input('请输入你感兴趣的问题')
    with st.expander('补充提问回答'):
        if prompt:
            message, my_data_problem = manual_chat(agent_data_analyst,prompt)
            message.write(my_data_problem)
            state_new_info += my_data_problem
        else:
            st.write(" ")
    
