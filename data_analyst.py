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


"""
#@st.cache_data 
#@st.cache_data 
def data_analysis(agent_data_analyst):
    questions = [
        "**最近七天除了unnamed开头的列，还有没有否缺失数据，缺失情况如何?**",
        "**最近七天，室内温度和湿度稳定性如何？**",
        "**最近七天，CO2浓度变化规律如何**",
        "**最近七天，pH变化规律如何**",
        "**最近七天，EC变化规律如何**",
    ]
    
    avatar = ':material/cruelty_free:'
    combined_info = ""
    
    for question in questions:
        st.write(question)
        message = st.chat_message(name="ai", avatar=avatar)
        
        prompt = f"""
请用中文简洁地回答以下问题:
        
{question}
        
要求:
1. 只使用2-3个最关键的数据点来回答问题
2. 直接给出结论,不需要详细解释过程
3. 回答应简明扼要,不超过3句话
4. 如果可能,请提供一个简短的建议或见解
5. 返回的JSON需要用markdown代码块包裹

请确保您的回答简洁,直接,并聚焦于最重要的信息
"""

        answer = agent_data_analyst.run(prompt)
    message.write(answer)
    combined_info += f"{question}\n{answer}\n\n"
    
    # 生成总结报告
    summary_prompt = f"""
基于以下分析结果,请生成一个中文的简洁的总结报告:

1. 总结报告应包含3-5个最重要的发现
2. 每个发现用一句话概括
3. 最后提供1-2个整体建议
4. 返回的JSON需要用markdown代码块包裹

请确保总结报告简洁明了,突出关键信息.

分析结果:
{combined_info}
"""
    
    summary = agent_data_analyst.run(summary_prompt)
    
    st.write("**总结报告**")
    message = st.chat_message(name="ai", avatar=':material/cruelty_free:')
    message.write(summary)
    
    return combined_info, summary
"""

@st.cache_resource
def manual_chat(agent_data_analyst,prompt):
    my_data_problem = agent_data_analyst.run(prompt)
    avatar = ':material/cruelty_free:'
    message = st.chat_message(name="ai",
                            avatar=avatar
                            )
    return message, my_data_problem
"""
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
"""



def data_analysis(agent_data_analyst):
    questions = [
        "**最近七天除了unnamed开头的列，还有没有否缺失数据，缺失情况如何?**",
        "**最近七天，室内温度和湿度稳定性如何？**",
        "**最近七天，CO2浓度变化规律如何**",
        "**最近七天，pH变化规律如何**",
        "**最近七天，EC变化规律如何**",
    ]
    
    avatar = ':material/cruelty_free:'
    combined_info = ""
    
    for question in questions:
        try:
            st.write(question)
            message = st.chat_message(name="ai", avatar=avatar)
            
            answer = agent_data_analyst.run(f"""
            请用中文简洁地回答以下问题:
            
            {question}
            
            要求:
            1. 只使用2-3个最关键的数据点来回答问题。
            2. 直接给出结论,不需要详细解释过程。
            3. 回答应简明扼要,不超过3句话。
            4. You must always return valid JSON fenced by a markdown code block. Do not return any additional text
            
            请确保您的回答简洁、直接,并聚焦于最重要的信息。
            """)
            
            message.write(answer)
            combined_info += question + "\n" + str(answer) + "\n\n"
            
        except Exception as e:
            error_msg = f"分析问题 '{question}' 时发生错误: {str(e)}"
            st.warning(error_msg)
            # 继续处理下一个问题，而不是完全停止
            continue
    
    # 生成总结报告
    try:
        summary_prompt = f"""
        基于以下分析结果,请生成一个中文的简洁的总结报告:
        
        1. 总结报告应包含3-5个最重要的发现。
        2. 每个发现用一句话概括。
        3. 最后提供1-2个整体建议。
        4. You must always return valid JSON fenced by a markdown code block. Do not return any additional text
        
        请确保总结报告简洁明了,突出关键信息。
        
        分析结果:
        {combined_info}
        """
        
        summary = agent_data_analyst.run(summary_prompt)
        
        st.write("**总结报告**")
        message = st.chat_message(name="ai", avatar=':material/cruelty_free:')
        message.write(summary)
        
    except Exception as e:
        st.error(f"生成总结报告时出现错误: {str(e)}")
    
    return combined_info, summary

def ai_assistants(df):
    try:
        agent_data_analyst = create_pandas_dataframe_agent(
            moonshot_llm,
            df,
            verbose=True,
            allow_dangerous_code=True
        )
        
        data_analysis(agent_data_analyst)
        
        prompt = st.chat_input('请输入你感兴趣的问题')
        with st.expander('补充提问回答'):
            if prompt:
                try:
                    message, my_data_problem = manual_chat(agent_data_analyst, prompt)
                    message.write(my_data_problem)
                except Exception as e:
                    st.error(f"处理提问时出现错误: {str(e)}")
            else:
                st.write(" ")
                
    except Exception as e:
        st.error(f"创建数据分析代理时出现错误: {str(e)}")


