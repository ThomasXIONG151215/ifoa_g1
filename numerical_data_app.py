import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta
import os
from st_files_connection import FilesConnection

def load_data(conn):
    try:
        return conn.read("ifoag1/integral_data.csv", input_format="csv", ttl=600)
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

    # 按类型分组列
    column_groups = {
        '温度': ['Temperature', 'Temperature1', 'Temperature2', 'Temperature3'],
        '湿度': ['Humidity', 'Humidity1', 'Humidity2', 'Humidity3'],
        'CO2': ['CO2PPM'],
        '水质': ['pH'],
        '水位': ['Wlevel']
    }

    # 为每个组创建图表
    for group, columns in column_groups.items():
        fig = go.Figure()
        valid_columns = [col for col in columns if col in filtered_df.columns]
        
        if not valid_columns:
            st.warning(f"没有找到 {group} 的有效数据。")
            continue
        
        for column in valid_columns:
            y_data = filtered_df[column].dropna()
            if not y_data.empty:
                fig.add_trace(go.Scatter(x=filtered_df['DateTime'], y=y_data, mode='lines', name=column))
        
        if len(fig.data) > 0:  # 只有在有数据时才显示图表
            y_values = [trace.y for trace in fig.data]
            y_max = max([max(y) if len(y) > 0 else 0 for y in y_values])
            y_min = min([min(y) if len(y) > 0 else 0 for y in y_values])
            
            if y_max > y_min:
                fig.update_layout(
                    title=f'{group}数据',
                    xaxis_title='日期时间',
                    yaxis_title='数值',
                    yaxis=dict(range=[max(0, y_min * 0.9), y_max * 1.1]),  # 设置y轴从0或略低于最小值开始
                    legend_title='传感器',
                    height=600,  # 增加高度以提高可视性
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"{group}数据全为常数或没有有效数据。")

    # 添加摘要统计表
    st.subheader("摘要统计")
    summary_df = filtered_df[list(sum(column_groups.values(), []))].describe()
    st.dataframe(summary_df)

    # 添加数据下载按钮
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="下载CSV数据",
        data=csv,
        file_name="plant_factory_data.csv",
        mime="text/csv",
    )

def main():
    st.set_page_config(
        page_title='室墨司源',
        layout='wide')
    st.title("司源中控平台")

    st.sidebar.image("logo.svg", use_column_width=True)
    
    #st.title("植物工厂数据查看器和设置编辑器")

    conn = st.connection('s3', type=FilesConnection)

    # 加载数据和设置
    df = load_data(conn)
    settings = load_settings(conn)

    if settings is None:
        st.error("加载设置失败。请检查您的S3配置。")
        return

    # 为设置编辑器和数据查看器创建标签页
    tab1, tab2 = st.tabs(["设置编辑器", "数据查看器"])

    with tab1:
        settings_editor(conn, settings)

    with tab2:
        data_viewer(df)

if __name__ == "__main__":
    main()
