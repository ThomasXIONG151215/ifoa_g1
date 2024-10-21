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
from PIL import Image
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

def improve_green_detection(image):
    # 转换到LAB色彩空间
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    
    # 分离L, A, B通道
    l, a, b = cv2.split(lab)
    
    # 对A通道应用阈值处理，A通道中绿色为负值
    _, thresh = cv2.threshold(a, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 使用腐蚀和膨胀操作来代替形态学开运算
    kernel = np.ones((3,3), np.uint8)
    eroded = cv2.erode(thresh, kernel, iterations=2)
    dilated = cv2.dilate(eroded, kernel, iterations=2)
    
    return dilated

def calculate_green_area_and_contour(image):
    mask = improve_green_detection(image)
    
    # 寻找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 过滤小的轮廓
    min_contour_area = 500  # 可以根据需要调整这个值
    filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
    
    # 创建一个新的掩码，只包含过滤后的轮廓
    filtered_mask = np.zeros(mask.shape, dtype=np.uint8)
    cv2.drawContours(filtered_mask, filtered_contours, -1, 255, -1)
    
    contour_image = image.copy()
    cv2.drawContours(contour_image, filtered_contours, -1, (0, 255, 0), 2)
    
    # 只计算过滤后的绿色区域面积
    green_area = np.sum(filtered_mask > 0)
    
    return green_area, contour_image, filtered_mask

def process_image(image_url):
    response = requests.get(image_url)
    image = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
    
    green_area, contour_image, filtered_mask = calculate_green_area_and_contour(image)
    
    # 使用过滤后的掩码来只显示主要的绿色区域
    result_image = cv2.bitwise_and(image, image, mask=filtered_mask)
    
    # 在结果图像上绘制轮廓
    cv2.drawContours(result_image, cv2.findContours(filtered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], -1, (0, 255, 0), 2)
    
    # 转换为PIL Image以便Streamlit显示
    result_image_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(result_image_rgb)
    
    return green_area, pil_image




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
    #leaf_area_data = process_images_and_store_data(image_list)

    # Plot leaf area over time
    #plot_image = plot_leaf_area_over_time(leaf_area_data)
    #st.image(plot_image, caption='Green Leaf Area Over Time')
  
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
                
                green_area, processed_image = process_image(image_url)
                
                with col2:
                    st.image(processed_image)
                    st.write(f"处理后图片 (绿色轮廓): {image_date}")
                
                st.write(f"绿叶面积: {green_area} 像素")
    else:
        st.warning("未找到匹配的图片。")

