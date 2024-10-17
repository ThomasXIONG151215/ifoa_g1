import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import re

import numpy as np
import requests
import time
#import threading
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
        "**请对当前种植情况做一个整体评价**",
        "**当前室内温度对作物的影响如何？**",
        "**当前CO2浓度是否在最优区间内?对植物生长有何影响?**",
        "**目前的光照强度是否适宜?是否需要调整?**",
        "**湿度水平如何?是否在植物生长的理想范围内?**",
        "**基于当前数据,您对未来一周的产量有何预测?**",
        "**有哪些关键指标需要特别关注或改进?**"
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

    # 将DateTime列转换为datetime类型
    df['DateTime'] = pd.to_datetime(df['DateTime_y'])

    # 时间范围选择器
    date_range = st.date_input(
        "选择日期范围",
        [df['DateTime'].min().date(), df['DateTime'].max().date()]
    )
    start_date, end_date = date_range
    mask = (df['DateTime'].dt.date >= start_date) & (df['DateTime'].dt.date <= end_date)
    filtered_df = df.loc[mask]

    # 数据清理函数
    def clean_data(series):
        # 移除-1值
        series = series[series != -1]
        
        # 移除异常值（使用IQR方法）
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return series[(series >= lower_bound) & (series <= upper_bound)]


    # 按类型分组列
    column_groups = {
        '温度': ['Temperature', 'Temperature1', 'Temperature2', 'Temperature3','TempA','TempB','TempC','WTEMP'],
        '湿度': ['Humidity', 'Humidity1', 'Humidity2', 'Humidity3', 'HumiA','HumiB','HumiC'],
        'CO2': ['CO2PPM','CO2PPM1','CO2PPM2','CO2PPM3','CO2PPMA','CO2PPMB','CO2PPMC'],
        '水质': ['pH', 'EC'],  # 添加EC
        '水位': ['Wlevel']
    }

    # 为每个组创建图表
    for group, columns in column_groups.items():
        fig = go.Figure()
        valid_data = False
        for column in columns:
            if column in filtered_df.columns:
                # 清理数据
                clean_series = clean_data(filtered_df[column])
                if not clean_series.empty:
                    fig.add_trace(go.Scatter(x=filtered_df.loc[clean_series.index, 'DateTime'], 
                                             y=clean_series, 
                                             mode='lines', 
                                             name=column))
                    valid_data = True
        
        if valid_data:
            y_max = max([trace.y.max() for trace in fig.data])
            y_min = min([trace.y.min() for trace in fig.data])
            fig.update_layout(
                title=f'{group}数据',
                xaxis_title='日期时间',
                yaxis_title='数值',
                yaxis=dict(range=[max(0, y_min * 0.9), y_max * 1.1]),  # 调整y轴范围，确保不会出现负值
                legend_title='传感器',
                height=600,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"没有找到 {group} 的有效数据。")

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


def calculate_green_area(image_url):
    # Download the image from the URL
    resp = requests.get(image_url)
    image = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
    
    # Convert to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Define range of green color in HSV
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])
    
    # Create a mask for green color
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Calculate the area of green pixels
    green_area = np.sum(mask > 0)
    
    return green_area

def get_image_list(unit_number):
    try:
        prefix = f"images/{unit_number}/"
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        
        image_list = []
        for page in pages:
            for item in page.get('Contents', []):
                key = item['Key']
                if key.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filename = key.split('/')[-1]
                    if filename.startswith('img') or filename.startswith('img_dst'):
                        date = extract_date_from_filename(key)
                        if date:
                            image_type = 'original' if filename.startswith('img') and not filename.startswith('img_dst') else 'processed'
                            image_list.append((key, date, image_type))
        
        # 根据日期时间排序，最新的在前
        return sorted(image_list, key=lambda x: x[1], reverse=True)
    except ClientError as e:
        st.error(f"获取图片列表时出错: {str(e)}")
        return []



def process_images_and_store_data(image_list):
    data = []
    for image_key, image_date, image_type in image_list:
        if image_type == 'original':  # Only process original images
            image_url = s3_client.generate_presigned_url('get_object',
                                                         Params={'Bucket': S3_BUCKET_NAME,
                                                                 'Key': image_key},
                                                         ExpiresIn=3600)
            green_area = calculate_green_area(image_url)
            data.append((image_date, green_area))
    return data

def process_images_and_store_data(image_list):
    data = []
    for image_key, image_date, image_type in image_list:
        if image_type == 'original':  # Only process original images
            image_url = s3_client.generate_presigned_url('get_object',
                                                         Params={'Bucket': S3_BUCKET_NAME,
                                                                 'Key': image_key},
                                                         ExpiresIn=3600)
            green_area = calculate_green_area(image_url)
            data.append((image_date, green_area))
    return data

import io
def plot_leaf_area_over_time(data):
    dates = [d[0] for d in data]
    areas = [d[1] for d in data]
    
    plt.figure(figsize=(10, 6))
    plt.plot(dates, areas, marker='o')
    plt.title('Green Leaf Area Over Time')
    plt.xlabel('Date')
    plt.ylabel('Green Leaf Area (pixels)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Convert plot to image
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

def image_viewer():
    st.header("图片查看器")

    available_units = get_available_units()

    if not available_units:
        st.warning("没有找到任何图片单元。")
        return

    # 使用会话状态来记住选择的单元，但确保它仍然有效
    if 'selected_unit' not in st.session_state or st.session_state.selected_unit not in available_units:
        st.session_state.selected_unit = available_units[0]

    unit_number = st.selectbox("选择单元编号", available_units, key='unit_selector', index=available_units.index(st.session_state.selected_unit))
    
    # 如果单元改变，重置日期和时间选择
    if unit_number != st.session_state.selected_unit:
        st.session_state.selected_unit = unit_number
        st.session_state.pop('selected_date', None)
        st.session_state.pop('selected_time', None)

    image_list = get_image_list(unit_number)

    if not image_list:
        st.warning(f"单元 {unit_number} 没有可用的图片。")
        return

    # Process images and get leaf area data
    leaf_area_data = process_images_and_store_data(image_list)

    # Plot leaf area over time
    plot_image = plot_leaf_area_over_time(leaf_area_data)
    st.image(plot_image, caption='Green Leaf Area Over Time')
  
    # 获取所有可用的日期
    available_dates = sorted(set(image[1].date() for image in image_list), reverse=True)

    # 使用会话状态来记住选择的日期，但确保它仍然有效
    if 'selected_date' not in st.session_state or st.session_state.selected_date not in available_dates:
        st.session_state.selected_date = available_dates[0]

    # 日期选择器
    selected_date = st.date_input("选择日期", value=st.session_state.selected_date, key='date_selector')
    
    # 如果日期改变，重置时间选择
    if selected_date != st.session_state.selected_date:
        st.session_state.selected_date = selected_date
        st.session_state.pop('selected_time', None)

    # 筛选选定日期的图片
    filtered_images = [img for img in image_list if img[1].date() == selected_date]

    if not filtered_images:
        st.warning(f"在 {selected_date} 没有可用的图片。")
        return

    # 获取选定日期的所有可用时间
    available_times = sorted(set(image[1].time() for image in filtered_images), reverse=True)

    # 使用会话状态来记住选择的时间，但确保它仍然有效
    if 'selected_time' not in st.session_state or st.session_state.selected_time not in available_times:
        st.session_state.selected_time = available_times[0]

    # 时间选择器
    selected_time = st.selectbox("选择时间", 
                                 options=available_times,
                                 format_func=lambda x: x.strftime("%H:%M:%S"),
                                 key='time_selector', 
                                 index=available_times.index(st.session_state.selected_time))
    st.session_state.selected_time = selected_time

    # 找到匹配的图片
    matching_images = [img for img in filtered_images if img[1].time() == selected_time]

    if matching_images:
        col1, col2 = st.columns(2)
        for img in matching_images:
            image_key, image_date, image_type = img
            image_url = s3_client.generate_presigned_url('get_object',
                                                         Params={'Bucket': S3_BUCKET_NAME,
                                                                 'Key': image_key},
                                                         ExpiresIn=3600)
            if image_type == 'original':
                with col1:
                    st.image(image_url)
                    st.write(f"原始图片: {image_date}")
            else:
                with col2:
                    st.image(image_url)
                    st.write(f"处理后图片: {image_date}")
            
            #green_area = calculate_green_area(image_url)
            #st.write(f"绿叶面积: {green_area} 像素")


                
  
    else:
        st.warning("未找到匹配的图片。")
