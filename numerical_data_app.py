import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import re
from st_files_connection import FilesConnection
import streamlit.components.v1 as components
from langchain_community.llms import Tongyi
from langchain_community.llms.moonshot import Moonshot
from langchain_experimental.agents import create_pandas_dataframe_agent
import numpy as np
import requests
import time
import matplotlib.pyplot as plt 
import cv2
from data_analyst import ai_assistants
st.set_page_config(page_title='室墨司源', layout='wide')

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


def settings_editor(conn, settings):
    new_settings = settings.copy()
    
    st.header("设置编辑器")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 光照设置
        st.subheader("光照")
        new_settings['lighting']['on_time'] = st.time_input("开灯时间", datetime.strptime(settings['lighting'].get('on_time', '06:00'), "%H:%M").time())
        new_settings['lighting']['off_time'] = st.time_input("关灯时间", datetime.strptime(settings['lighting'].get('off_time', '22:00'), "%H:%M").time())
        
        for i in range(4):
            new_settings['lighting'][f'led_intensity_{i+1}'] = st.slider(f"LED灯排 {i+1} 强度 (%)", 0, 100, settings['lighting'].get(f'led_intensity_{i+1}', 50))

        # 策略
        st.subheader("策略")
        new_settings['strategy'] = st.selectbox("控制策略", ["经典内循环", "新风外循环", "混合双循环"], index=["经典内循环", "新风外循环", "混合双循环"].index(settings['strategy']))

    with col2:
        # 环境设置
        st.subheader("环境")
        for period in ['light_period', 'dark_period']:
            st.write("光照期" if period == 'light_period' else "黑暗期")
            new_settings['environment'][period]['temperature_celsius'] = st.slider(f"温度 (°C) - {'光照期' if period == 'light_period' else '黑暗期'}", 0, 40, settings['environment'][period]['temperature_celsius'])
            new_settings['environment'][period]['humidity_percentage'] = st.slider(f"湿度 (%) - {'光照期' if period == 'light_period' else '黑暗期'}", 0, 100, settings['environment'][period]['humidity_percentage'])
            new_settings['environment'][period]['co2_ppm'] = st.slider(f"CO2 (ppm) - {'光照期' if period == 'light_period' else '黑暗期'}", 0, 2000, settings['environment'][period]['co2_ppm'])

        # 灌溉设置
        st.subheader("灌溉")
        new_settings['irrigation']['frequency_hours'] = st.number_input("灌溉频率 (小时)", 0.1, 24.0, float(settings['irrigation']['frequency_hours']), 0.1)
        new_settings['irrigation']['duration_minutes'] = st.number_input("灌溉时长 (分钟)", 1, 60, int(settings['irrigation']['duration_minutes']), 1)

        # 营养液设置
        st.subheader("营养液")
        new_settings['nutrient_solution']['ec_ms_cm'] = st.number_input("电导率 EC (mS/cm)", 0.1, 5.0, float(settings['nutrient_solution']['ec_ms_cm']), 0.1)
        new_settings['nutrient_solution']['ph'] = st.number_input("pH值", 0.0, 14.0, float(settings['nutrient_solution']['ph']), 0.1)

    # 更新设置
    if st.button("更新设置"):
        save_settings(conn, new_settings)



def data_viewer(df):
    st.header("数据查看器")
    
    if df is None or df.empty:
        st.warning("没有可用的数据进行可视化。")
        return

    df['DateTime'] = pd.to_datetime(df['DateTime_y'])
    
    date_range = st.date_input(
        "选择日期范围",
        [df['DateTime'].min().date(), df['DateTime'].max().date()]
    )
    start_date, end_date = date_range
    mask = (df['DateTime'].dt.date >= start_date) & (df['DateTime'].dt.date <= end_date)
    filtered_df = df.loc[mask]

    def clean_data(series, simple_clean=True):
      # 移除-1值
      series = series[series != -1]
      
      if simple_clean or len(series) <= 100:
          # 数据量小于等于1000时，只去除-1值
          return series
      else:
          # 数据量大时，使用完整的异常值清洗
          Q1 = series.quantile(0.25)
          Q3 = series.quantile(0.75)
          IQR = Q3 - Q1
          lower_bound = Q1 - 1.5 * IQR
          upper_bound = Q3 + 1.5 * IQR
          return series[(series >= lower_bound) & (series <= upper_bound)]

    column_groups = {
        '温度': ['Temperature', 'Temperature1', 'Temperature2', 'Temperature3','TempA','TempB','TempC','WTEMP'],
        '湿度': ['Humidity', 'Humidity1', 'Humidity2', 'Humidity3', 'HumiA','HumiB','HumiC'],
        'CO2': ['CO2PPM','CO2PPM1','CO2PPM2','CO2PPM3','CO2PPMA','CO2PPMB','CO2PPMC'],
        'EC': ['EC'],
        'pH': ['pH'],
        '水位': ['Wlevel']
    }

    for group, columns in column_groups.items():
        st.subheader(f'{group}数据')
        
        # 找出第一个有效的列
        valid_columns = [col for col in columns if col in filtered_df.columns]
        if not valid_columns:
            st.warning(f"没有找到 {group} 的有效数据。")
            continue
        
        # 创建多选框，默认选中第一个有效列
        selected_columns = st.multiselect(
            f"选择要显示的 {group} 数据列",
            options=valid_columns,
            default=[valid_columns[0]]
        )

        if selected_columns:
            fig = go.Figure()
            for column in selected_columns:
                # 检查数据量
                data_series = filtered_df[column]
                # 仅去除-1值
                clean_series = data_series[data_series != -1]
                
                if not clean_series.empty:
                    fig.add_trace(go.Scatter(x=filtered_df.loc[clean_series.index, 'DateTime'], 
                                            y=clean_series, 
                                            mode='lines', 
                                            name=column))

            y_max = max([trace.y.max() for trace in fig.data])
            y_min = min([trace.y.min() for trace in fig.data])
            fig.update_layout(
                xaxis_title='日期时间',
                yaxis_title='数值',
                yaxis=dict(range=[max(0, y_min * 0.9), y_max * 1.1]),
                legend_title='传感器',
                height=600,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"请选择至少一个 {group} 数据列进行显示。")

    # 添加摘要统计表
    st.subheader("摘要统计")
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    
    # 创建一个新的DataFrame来存储清理后的摘要统计
    summary_df = pd.DataFrame()
    
    for column in numeric_columns:
        clean_series = clean_data(df[column])
        if not clean_series.empty:
            summary_df[column] = clean_series.describe()
    
    st.dataframe(summary_df)

    # 添加数据下载按钮
    csv = filtered_df.to_csv(index=False)
    #st.download_button(
    #    label="下载CSV数据",
    #    data=csv,
    #    file_name="plant_factory_data.csv",
    #    mime="text/csv",
    #)


    
def get_available_units():
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix="images/", Delimiter='/')
        units = []
        for prefix in response.get('CommonPrefixes', []):
            prefix_name = prefix.get('Prefix', '')
            unit = prefix_name.strip('/').split('/')[-1]
            if unit:
                units.append(unit)
        return sorted(units)
    except ClientError as e:
        st.error(f"获取可用单元列表时出错: {str(e)}")
        return []

def extract_date_from_filename(filename):
    pattern = r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})"
    match = re.search(pattern, filename)
    if match:
        date_str = match.group(1)
        return datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
    return None

from visual_data_process import image_viewer
      
def overview_tab(df):
    st.header("综合概览")

    col1, col2 = st.columns([7, 3])

    with col1:
        image_viewer()

    with col2:
        st.subheader("最新环境数据")
        
        if df is not None and not df.empty:
            latest_data = df.iloc[-1]
            previous_data = df.iloc[-2] if len(df) > 1 else latest_data

            # 温度
            temperature_diff = latest_data['Temperature'] - previous_data['Temperature']
            st.metric(label="温度 (°C)", 
                      value=f"{latest_data['Temperature']:.1f}",
                      delta=f"{temperature_diff:.1f}")

            # 湿度
            humidity_diff = latest_data['Humidity'] - previous_data['Humidity']
            st.metric(label="湿度 (%)", 
                      value=f"{latest_data['Humidity']:.1f}",
                      delta=f"{humidity_diff:.1f}")

            # CO2 (如果有的话)
            if 'CO2PPM' in df.columns:
                co2_diff = latest_data['CO2PPM'] - previous_data['CO2PPM']
                st.metric(label="CO2 (ppm)", 
                          value=f"{latest_data['CO2PPM']:.0f}",
                          delta=f"{co2_diff:.0f}")

            # pH值
            if 'pH' in df.columns:
                ph_diff = latest_data['pH'] - previous_data['pH']
                ph_value = latest_data['pH']
                st.metric(label="pH值", 
                          value=f"{ph_value:.2f}",
                          delta=f"{ph_diff:.2f}")
                
                # pH警告
                if ph_value < 5 or ph_value > 7:
                    st.warning(f"警告：pH值 ({ph_value:.2f}) 超出正常范围 (5-7)!")

            # EC值
            if 'EC' in df.columns:
                ec_diff = latest_data['EC'] - previous_data['EC']
                st.metric(label="EC值 (mS/cm)", 
                          value=f"{latest_data['EC']:.2f}",
                          delta=f"{ec_diff:.2f}")

        else:
            st.warning("无法加载最新的环境数据。")


#conn = st.connection('s3', type=FilesConnection)


def main():
    st.title("司源中控平台")
    
    conn = st.connection('s3', type=FilesConnection)
    
    # 加载设置
    settings = load_settings(conn)
    if settings is None:
        st.error("加载设置失败。请检查您的S3配置。")
        return

    # 创建标签页
    tab0, tab2, tab3 = st.tabs(["即时反馈面板", "历史数据查看", "生生AI问答"])

    # 添加刷新按钮
    if st.button("刷新数据"):
        st.rerun()

    # 加载最新数据
    df = load_data(conn)

    if df is not None:
        with tab0:
            overview_tab(df)

        #with tab1:
        #    settings_editor(conn, settings)

        with tab2:
            data_viewer(df)

        with tab3:
            ai_assistants(df)
    else:
        st.warning("数据加载失败，请检查网络连接或S3配置。")

    # 添加自动刷新功能
    st.write("页面将每5分钟自动刷新一次")
    time.sleep(300)  # 等待5分钟
    st.rerun()  # 重新运行整个应用

if __name__ == "__main__":
    main()


