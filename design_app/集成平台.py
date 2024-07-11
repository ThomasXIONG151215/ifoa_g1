import streamlit as st 
import pandas as pd
import requests
import json
from datetime import datetime
from datetime import timezone as tmz
import pytz
from tzwhere import tzwhere
import folium
from streamlit_folium import folium_static
from plotly.subplots import make_subplots
import plotly.graph_objs as go

st.set_page_config(page_title="室墨司源",
                   page_icon="🏠",
                   layout="wide",
                   )

st.title('室墨司源智设运维平台')

# 左边侧栏是目标的重要性权重；而且一直保持在那里
# 产量
# 能耗
# 成本

# 右边根据结果显示

kb, tab1, tab2, tab3, mp,tab4 = st.tabs(["综合知识库","布局规划","环境结构设计","能源系统设计","市场产品匹配","远程可控制面板"])


st.sidebar.header('植物工厂定制栏')

st.sidebar.subheader('目标种植')

specy = st.sidebar.selectbox('选择生菜品种', ['奶油','意大利','大速生'])


file = "streamlit-weather-app-main/worldcities.csv"
data = pd.read_csv(file)


st.sidebar.subheader('性能权重')

production = st.sidebar.slider('产量', 0, 100, 50)

energy_consumption = st.sidebar.slider('能耗', 0, 100, 50)

material_cost = st.sidebar.slider('成本', 0, 100, 50)


# Select Country
countries = ['China','France', 'Iraq', 'Vanuatu', 'Russia', 'Georgia', 'Qatar']
country_set = set(countries) #set(data.loc[:,"country"])

st.sidebar.subheader('选择种植地点')

country = st.sidebar.selectbox('选择国家/地区', options=country_set,index=6)

country_data = data.loc[data.loc[:,"country"] == country,:]

city_set = country_data.loc[:,"city_ascii"] 

with kb:
    st.header('综合知识库')
    st.write('这里汇集不同理工科和生物学科的知识和已知数据库')
    #st.header('目录导航')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.page_link("pages/建筑设计.py",label='建筑设计',icon='🏠')
        st.page_link("pages/人工光照.py",label='人工光照',icon='💡')
        st.page_link("pages/辐射制冷.py",label='辐射制冷',icon='❄️')
    with col2:
        st.page_link("pages/生菜种植.py",label='生菜种植',icon='🌱')
        st.page_link("pages/水泵.py",label='水泵',icon='🌊')
        st.page_link("pages/流体力学.py",label='流体力学',icon='🌊')
    with col3:
        st.page_link("pages/暖通空调.py",label='暖通空调',icon='❄️')
        st.page_link("pages/实时控制.py",label='智能控制算法',icon='🧠')
        
    #with 
    
    
    # 生物学
    ## 植物蒸腾作用
    ## 植物光合作用
    ## 生菜数据库
    ## 植物生长模型 源代码
    
    # 人工
    
    # 暖通空调
    ## 经典负荷模型
    ## 建筑热平衡与水分平衡要点
    ## 控制算法口诀
    ## 空调数据库
        
    # 建筑设计
    ## 关于grasshopper/Rhino
    ## 钢材数据库
    
    # 其它市面产品
    ## LED灯产品数据库
    ## 水泵产品数据库

with tab1:
    st.header('布局规划')
    # 知识库

    # 上面是崇明气候热力图；不同可选地区
    # 下面选择植物品种；
    # 然后


    # 优化调度
    ## 上面有历史数据，实现是历史数据，虚线是预测数据
    ## 优化调度下边有按钮，
    #

    city = st.selectbox('选择城市', options=city_set, index=1)
    #location = st.sidebar.selectbox('种植地点', ['上海崇明','上海闵行','北京海淀'])

    lat = float(country_data.loc[data.loc[:,"city_ascii"] == city, "lat"])
    lng = float(country_data.loc[data.loc[:,"city_ascii"] == city, "lng"])

    response_current = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current_weather=true')

    st.subheader("当前气候")

    result_current = json.loads(response_current._content)

    current = result_current["current_weather"]
    temp = current["temperature"]
    speed = current["windspeed"]
    direction = current["winddirection"]

    # Increment added or substracted from degree values for wind direction
    ddeg = 11.25

    # Determine wind direction based on received degrees
    if direction >= (360-ddeg) or direction < (0+ddeg):
        common_dir = "N"
    elif direction >= (337.5-ddeg) and direction < (337.5+ddeg):
        common_dir = "N/NW"
    elif direction >= (315-ddeg) and direction < (315+ddeg):
        common_dir = "NW"
    elif direction >= (292.5-ddeg) and direction < (292.5+ddeg):
        common_dir = "W/NW"
    elif direction >= (270-ddeg) and direction < (270+ddeg):
        common_dir = "W"
    elif direction >= (247.5-ddeg) and direction < (247.5+ddeg):
        common_dir = "W/SW"
    elif direction >= (225-ddeg) and direction < (225+ddeg):
        common_dir = "SW"
    elif direction >= (202.5-ddeg) and direction < (202.5+ddeg):
        common_dir = "S/SW"
    elif direction >= (180-ddeg) and direction < (180+ddeg):
        common_dir = "S"
    elif direction >= (157.5-ddeg) and direction < (157.5+ddeg):
        common_dir = "S/SE"
    elif direction >= (135-ddeg) and direction < (135+ddeg):
        common_dir = "SE"
    elif direction >= (112.5-ddeg) and direction < (112.5+ddeg):
        common_dir = "E/SE"
    elif direction >= (90-ddeg) and direction < (90+ddeg):
        common_dir = "E"
    elif direction >= (67.5-ddeg) and direction < (67.5+ddeg):
        common_dir = "E/NE"
    elif direction >= (45-ddeg) and direction < (45+ddeg):
        common_dir = "NE"
    elif direction >= (22.5-ddeg) and direction < (22.5+ddeg):
        common_dir = "N/NE"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('气温',value=temp, delta=-0.1, delta_color='normal')
    
    with col2:
        st.metric('风速',value=speed, delta=0.1, delta_color='normal')
        
    with col3:
        st.metric('风向', value=common_dir, delta=0.1, delta_color='normal')
    
    st.subheader("一周预测")

    st.write('预测后面一周的温度和降水量', unsafe_allow_html=True)

    with st.spinner('Loading...'):
        response_hourly = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&hourly=temperature_2m,precipitation')
        result_hourly = json.loads(response_hourly._content)
        hourly = result_hourly["hourly"]
        hourly_df = pd.DataFrame.from_dict(hourly)
        hourly_df.rename(columns = {'time':'Week ahead'}, inplace = True)
        hourly_df.rename(columns = {'temperature_2m':'Temperature °C'}, inplace = True)
        hourly_df.rename(columns = {'precipitation':'Precipitation mm'}, inplace = True)
        
        tz = tzwhere.tzwhere(forceTZ=True)
        timezone_str = tz.tzNameAt(lat, lng, forceTZ=True) # Seville coordinates
        
        timezone_loc = pytz.timezone(timezone_str)
        dt = datetime.now()
        tzoffset = timezone_loc.utcoffset(dt)#-timedelta(hours=1,minutes=0)
        
        
        # Create figure with secondary y axis
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        
        
        week_ahead = pd.to_datetime(hourly_df['Week ahead'],format="%Y-%m-%dT%H:%M")
        
        # Add traces
        fig.add_trace(go.Scatter(x = week_ahead+tzoffset, 
                                y = hourly_df['Temperature °C'],
                                name = "Temperature °C"),
                    secondary_y = False,)
        
        fig.add_trace(go.Bar(x = week_ahead+tzoffset, 
                            y = hourly_df['Precipitation mm'],
                            name = "Precipitation mm"),
                    secondary_y = True,)
        
        time_now = datetime.now(tmz.utc)+tzoffset
        
        fig.add_vline(x = time_now, line_color="red", opacity=0.4)
        fig.add_annotation(x = time_now, y=max(hourly_df['Temperature °C'])+5,
                    text = time_now.strftime("%d %b %y, %H:%M"),
                    showarrow=False,
                    yshift=0)
        
        fig.update_yaxes(range=[min(hourly_df['Temperature °C'])-10,
                                max(hourly_df['Temperature °C'])+10],
                        title_text="Temperature °C",
                        secondary_y=False,
                        showgrid=False,
                        zeroline=False)
            
        fig.update_yaxes(range=[min(hourly_df['Precipitation mm'])-2,
                                max(hourly_df['Precipitation mm'])+8], 
                        title_text="Precipitation (rain/showers/snow) mm",
                        secondary_y=True,
                        showgrid=False)
        
        
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.7
        ))
        
        # center on Liberty Bell, add marker
        m = folium.Map(location=[lat, lng], zoom_start=7)
        folium.Marker([lat, lng], 
                popup=city+', '+country, 
                tooltip=city+', '+country).add_to(m)
        
        # call to render Folium map in Streamlit
        
        # Make folium map responsive to adapt to smaller display size (
        # e.g., on smartphones and tablets)
        make_map_responsive= """
        <style>
        [title~="st.iframe"] { width: 100%}
        </style>
        """
        st.markdown(make_map_responsive, unsafe_allow_html=True)
        
        # Display chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Display map
        st_data = folium_static(m, height = 370)
        
        
        # Concluding remarks
        st.write('气候数据来源: [http://open-meteo.com](http://open-meteo.com) \n\n')


        #pv.start_xvfb()
        #根据侧栏选择的品种调用相应的生菜模型
        #plotter = pv.Plotter(border=False, window_size=(800, 600))
        #plotter.background_color = 'black'
        #reader = pv.STLReader('')
        #mesh = reader.read()
        
        
        
import threading
import base64
import time

def show_gif():
    #global stop_operation
    file_ = open("test_gif.gif", "rb")
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    file_.close()
    
    #while not stop_operation:
    st.markdown(
        f'<img src="data:image/gif;base64,{data_url}" alt="cat gif">',
        unsafe_allow_html=True,
    )

def stop_after_n_seconds(n):
    global stop_operation
    time.sleep(n)
    stop_operation = True


with tab2:
    st.header('环境结构设计')
    
    st.subheader('确定植物工厂整体尺寸')
    
    L = st.number_input('整体长度', min_value=2.00, value=6.06, max_value=100.00, step=0.01)
    
    W = st.number_input('整体宽度', min_value=2.00, value=2.44, max_value=100.00, step=0.01)
    
    H = st.number_input('整体高度', min_value=2.00, value=2.59, max_value=50.00, step=0.01)
    
    Ratio = st.number_input('设备间与种植区之比', min_value=0.00, value=0.2, max_value=1.0, step=0.01)
    
    automate_design = st.button('点击开始设计')
    
    if automate_design:#看要么返回三维结构，要么先返回一个gif过程；然后再返回三维结构；然后再返回渲染图
        st.info('结构已生成')
    
        with st.expander('寻优可视化过程'):
            st.write('这是算法寻优过程')
            test = show_gif() 
        

        with st.expander('候选环境结构'):
            st.write('这里是候选环境结构')
        
        with st.expander('最终植物工厂最优结构'):
            st.write('这里是最终植物工厂最优结构')

            st.write('所生成结构的性能参数')
            
            st.write('光照分布')
            
            st.write('气流分布')
        
   # name = st.text_input('Name')
   # if not name:
    #    st.warning('Please input a name.')
     #   st.stop()
    #st.success('Thank you for inputting a name.')
    
    
    
with tab3:
    st.header('能源系统匹配')
    
    
    calc_loads = st.button('计算一年空调负荷')
    
    st.write('一年气候')
    
    
    
    st.write('一年负荷')
    
    
    
    st.subheader('能源系统寻优设计')
    
    search_opti = st.button('寻找最优能源系统参数')
    
    st.write('这是围护结构传热系数，cop，制冷量和光照效率')
    
    st.write('这是能源消耗估计')
    
    
with mp:
    st.header('市场产品匹配')
    st.write('一定阈值下匹配参数而且性价比最高的产品')


def control_pannel():
    st.markdown("## 控制面板")

    st.markdown("### 灯光控制")
    l1, l2 = st.columns(2)
    with l1:
        light_start = st.slider("开启时间",min_value=0,max_value=24,value=18)
        #blue = st.number_input("蓝光",min_value=0,max_value=100,value=20)
        #red = st.number_input("红光",min_value=0,max_value=100,value=40)
        #green = st.number_input("绿光",min_value=0,max_value=100,value=10)
        #large_red = st.number_input("远红光",min_value=0,max_value=100,value=10)
    with l2:
        #st.metric(label = "光照强度",value=str(round((blue+red+green+large_red)/4,1))+" %")
        light_end = st.slider("关闭时间",min_value=0,max_value=24,value=10)
    exec_light = st.button("灯光执行")
    if exec_light:
        light_lenght = 24 - light_start + light_end
        dark_lenght = 24 - light_lenght
        st.session_state.light = st.warning("执行成功，从现在起光期时长为"+str(light_lenght)+"小时, 暗期时长为"+str(dark_lenght)+"小时")

    st.markdown("### 温度控制")
    a1, a2 = st.columns(2)
    with a1:
        ac_onoff = st.checkbox("空调开关")
        T_set = st.number_input("设定温度",min_value=18,max_value=30,value=24)
        #fresh_air_onoff = st.checkbox("新风开关")
        mode = st.selectbox("模式",["制冷","制热","送风","除湿"])
        mode_effect = {
            "制冷": -1,
            "制热": 1,
            "送风": -0.1,
            "除湿": -0.5
        }[mode]
        intensity = st.number_input("风速档位",min_value=0,max_value=7,value=4)
        duration = st.number_input("持续时间(min)",min_value=0,max_value=60,value=2)
        #fresh_air_rate = st.number_input("新风开度",min_value=0,max_value=100,value=20)        
        T_now = 24.7
        T_predict = T_now + ac_onoff*mode_effect*intensity*duration/60
        
        RH_now = 67
        RH_predict = RH_now + ac_onoff*mode_effect*intensity*duration/60 * 3.2

    with a2:
        d1, d2 = st.columns(2)
        
        with d1:
            st.metric(label = "当前温度",value=str(round(T_now,1))+" ℃")
            st.metric(label = "预测温度",value=str(round(T_predict,1))+" ℃",delta=str(round(T_predict-T_now,1))+" ℃")
        
        with d2:
            st.metric(label = "当前湿度",value=str(round(RH_now,1))+" %")
            st.metric(label = "预测湿度",value=str(round(RH_predict,1))+" %",delta=str(round(RH_predict-RH_now,1))+" %")
        T_set_light = st.slider("光期设定温度",min_value=18,max_value=26,value=T_set)
        T_set_night = st.slider("暗期设定温度",min_value=17,max_value=26,value=22)

        ac_exec = st.button("空调执行")
    if ac_exec:
        st.success("执行成功，预计"+str(duration)+"分钟后温度达到"+str(T_predict)+"度与目标值"+str(T_set)+"度相差"+"%s ℃" % round(abs(T_predict-T_set),1)+"同时相对湿度温度维持在60-90%区间")

    st.markdown("### CO2控制")
    c1, c2 = st.columns(2)
    with c1:
        co2_set = st.number_input("CO2设定",min_value=0,max_value=1000,value=900)
        co2_duration = st.number_input("阀门开启时间(s)",min_value=0,max_value=120,value=30)
        step = st.number_input("规划次数",min_value=0,max_value=60,value=10)
        ppm_now = 700
        ppm_predict = ppm_now + step*co2_duration/60*32.4
    with c2:
        st.metric(label = "当前CO2浓度",value=str(ppm_now)+" ppm")
        st.metric(label = "预测CO2浓度",value=str(round(ppm_predict,1))+" ppm",delta=str(round(ppm_predict-ppm_now,1))+" ppm")
        co2_exec = st.button("CO2执行")
    if co2_exec:
        st.info("执行成功，预计二氧化碳浓度调节准确率将达"+"%s %%" % round(100-abs(ppm_predict-co2_set)/co2_set*100,1))

with tab4:
    
    control_pannel()
    
    
