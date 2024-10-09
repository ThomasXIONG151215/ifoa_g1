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
        conn.write("ifoag1/settings.json", json.dumps(settings, indent=2))
        st.success("设置更新成功!")
    except Exception as e:
        st.error(f"更新设置失败: {str(e)}")



@st.cache_data 
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
    summary_df = filtered_df[list(sum(column_groups.values(), []))].describe()
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
    # 假设文件名格式为 "YYYY-MM-DD_HH-MM-SS.jpg"
    pattern = r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})"
    match = re.search(pattern, filename)
    if match:
        date_str = match.group(1)
        return datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
    return None

def ai_assistants(df):
    agent_data_analyst = create_pandas_dataframe_agent(langchain_llm, df, verbose=True, allow_dangerous_code=True)
    with st.container(height=700):
        iframe_html = """
        <iframe src="https://udify.app/chatbot/QLSY0P3UgKlOifoO" 
                style="width: 100%; height: 700px;" 
                frameborder="0" 
                allow="microphone">
        </iframe>
        """
        components.html(iframe_html, height=700)

def get_image_list(unit_number):
    try:
        prefix = f"images/{unit_number}/"
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
        
        image_list = []
        for item in response.get('Contents', []):
            if item['Key'].lower().endswith(('.png', '.jpg', '.jpeg')):
                date = extract_date_from_filename(item['Key'])
                if date:
                    image_list.append((item['Key'], date))
        
        # 根据日期排序，最新的在前
        return sorted(image_list, key=lambda x: x[1], reverse=True)
    except ClientError as e:
        st.error(f"获取图片列表时出错: {str(e)}")
        return []

def image_viewer():
    st.header("图片查看器")

    available_units = get_available_units()

    if not available_units:
        st.warning("没有找到任何图片单元。")
        return

    unit_number = st.selectbox("选择单元编号", available_units)

    image_list = get_image_list(unit_number)

    if not image_list:
        st.warning(f"单元 {unit_number} 没有可用的图片。")
        return

    if len(image_list) > 1:
        index = st.slider("选择图片时间", 0, len(image_list) - 1, 0, key="image_slider")
    else:
        index = 0

    image_key, image_date = image_list[index]
    image_url = s3_client.generate_presigned_url('get_object',
                                                 Params={'Bucket': S3_BUCKET_NAME,
                                                         'Key': image_key},
                                                 ExpiresIn=3600)
    st.image(image_url)
    st.write(f"图片日期: {image_date}")

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
def main():
    st.set_page_config(page_title='室墨司源', layout='wide')
    st.title("司源中控平台")
    #st.sidebar.image("logo.svg", use_column_width=True)
    
    conn = st.connection('s3', type=FilesConnection)
    
    df = load_data(conn)
    settings = load_settings(conn)

    if settings is None:
        st.error("加载设置失败。请检查您的S3配置。")
        return

    tab0, tab1, tab2, tab3,  = st.tabs(["综合概览", "设置编辑器", "数据查看器", "AI助手团", #"图片查看器"
                              ])
    #tab4 
                   


    with tab0:
        overview_tab(df)

    with tab1:
        settings_editor(conn, settings)

    with tab2:
        data_viewer(df)

    with tab3:
        ai_assistants(df)

    #with tab4:
    #    image_viewer()

if __name__ == "__main__":
    main()


