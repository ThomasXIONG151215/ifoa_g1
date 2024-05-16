import streamlit as st
import numpy as np
from scipy.integrate import solve_ivp

# 页面配置
st.set_page_config(
    page_title="生菜种植知识库",
    page_icon="🌱",
    layout="wide",
)

st.title("生菜种植知识库")


# 创建标签页
tabs = st.tabs(["首页", "种植指南", "常见问题", "病虫害防治", "生菜品种", "植物生长模型", "团队交流"])

# 首页
with tabs[0]:
    st.write("""
    欢迎来到生菜种植知识库！作为一名拥有二十年农艺经验的专家，我将为您提供全面、详细的生菜种植指南。
    
    这个应用程序致力于分享生菜种植的实用技巧、解决常见问题的方法、病虫害防治策略以及各种生菜品种的介绍。希望这些知识能帮助您成功种植健康、美味的生菜。
""")

# 种植指南
with tabs[1]:
    st.header("种植指南")
    st.subheader("基本知识")
    st.write("""
        生菜是一种容易种植的蔬菜，适合家庭园艺和商业种植。生菜喜欢凉爽的气候，最佳生长温度为15-20摄氏度。种植生菜需要充足的阳光和排水良好的肥沃土壤。
    """)
    st.subheader("播种")
    st.write("""
        生菜种子可以直接播种在花园里或育苗盆中。种子应浅埋，每个种子之间保持10-15厘米的距离，以避免过度拥挤。播种后保持土壤湿润，但不要过于潮湿。
    """)
    st.subheader("移植")
    st.write("""
        当生菜苗长到3-4片真叶时，可以进行移植。移植时注意保持根系完整，栽种深度与育苗时相同。移植后及时浇水，以帮助植物适应新环境。
    """)
    st.subheader("养护")
    st.write("""
        生菜喜欢湿润的土壤，但不能积水。定期浇水，保持土壤湿润但不过湿。此外，定期松土和除草，有助于生菜的健康生长。生菜生长期间，可以施用适量的有机肥料，以提供必要的营养。
    """)
    st.subheader("光合作用和蒸腾作用")
    st.write("""
        生菜的生长离不开光合作用和蒸腾作用。
        
        **光合作用**是植物利用光能，将二氧化碳和水转化为葡萄糖和氧气的过程。这一过程发生在生菜的叶绿体中，需要充足的阳光。光合作用不仅为生菜提供能量，还释放氧气，改善周围环境的空气质量。

        **蒸腾作用**是植物通过叶片表面的气孔蒸发水分的过程。蒸腾作用有助于生菜调节体温，促进水分和养分的吸收和运输。适当的蒸腾作用有助于生菜的健康生长，但过度蒸腾可能导致水分流失过多，因此需要注意水分管理。
    """)

# 常见问题
with tabs[2]:
    st.header("常见问题")
    st.subheader("1. 为什么我的生菜叶子发黄？")
    st.write("""
        生菜叶子发黄可能是由于多种原因引起的，包括水分不足、土壤贫瘠或病虫害问题。首先，检查土壤湿度，确保生菜获得充足的水分。其次，可以施用适量的有机肥料，以改善土壤肥力。如果是病虫害引起的黄叶，需及时采取相应的防治措施。
    """)
    st.subheader("2. 生菜为什么长不大？")
    st.write("""
        生菜长不大可能是由于光照不足、种植密度过高或缺乏营养。生菜每天需要至少6小时的阳光，确保种植位置光照充足。此外，适当间苗，保持每株生菜之间有足够的生长空间。最后，施用适量的有机肥料，以提供生长所需的营养。
    """)

# 病虫害防治
with tabs[3]:
    st.header("病虫害防治")
    st.subheader("蚜虫")
    st.write("""
        蚜虫是生菜的常见害虫，主要危害生菜的嫩叶和幼茎。可以用肥皂水喷洒叶片，或使用生物农药进行防治。此外，种植一些驱蚜虫的植物，如薄荷或洋葱，也能有效减少蚜虫的数量。
    """)
    st.subheader("霉菌")
    st.write("""
        霉菌在潮湿环境中容易滋生，常见的霉菌病包括白粉病和灰霉病。防治霉菌的关键是保持良好的通风，避免过度浇水。发现霉菌病害时，可以使用适量的杀菌剂进行防治，同时及时移除受感染的植物部分。
    """)

# 生菜品种
with tabs[4]:
    st.header("生菜品种")
    st.subheader("罗马生菜")
    st.write("""
        罗马生菜（Romaine Lettuce）是一种直立的生菜品种，叶片厚实、质地脆嫩，适合制作各种沙拉。罗马生菜耐寒性较强，适合在较冷的气候条件下种植。
    """)
    st.subheader("奶油生菜")
    st.write("""
        奶油生菜（Butterhead Lettuce）质地柔软，口感细腻，适合制作三明治和沙拉。奶油生菜适应性强，可以在不同气候条件下生长。
    """)

# 植物生长模型
with tabs[5]:
    st.header("植物生长模型")
    st.write("""
        下面是基于2003年van Henten模型的植物生长模型源代码，用于模拟植物在不同环境条件下的生长过程。这个模型考虑了光合作用、蒸腾作用、通风和辐射等因素。
    """)
    st.code("""
import numpy as np
from scipy.integrate import solve_ivp

# 定义微分方程
def model(t, y, Qvent_q, Qrad_q, Vrad, Uv, Vh, constants):
    Xd, XT, Xh, Xc = y  # 解构当前的变量值
    cαβ, c_resp_d, c_resp_c, c_cap_q, c_cap_h, c_cap_c, Uc, c_rad_phot, c_co2_1, c_co2_2, c_co2_3, 
    cT_abs, c_leak, c_pl_d, c_v_pl_ai, c_v_1, c_v_2, c_v_3, c_R, cT = constants  # 解构常数

    # 计算 φ_phot_c
    φ_phot_c = (1 - np.exp(-c_rad_phot * Xd)) * c_rad_phot * Vrad * (-c_co2_1 * XT ** 2 + c_co2_2 * XT - c_co2_3) * (Xc - cT) / (
        c_rad_phot * Vrad + (-c_co2_1 * XT ** 2 + c_co2_2 * XT - c_co2_3) * (Xc - cT))

    φ_transp_h = (1 - np.exp(-c_pl_d * Xd)) * c_v_pl_ai * (c_v_1 * np.exp((c_v_2 * XT) / (XT + c_v_3)) / c_R * (XT + cT_abs) - Xh)

    φ_vent_h = (Uv + c_leak) * (Xh - Vh)
    # 计算 φ_vent_c
    φ_vent_c = (Uv + c_leak) * (Xc - Vc)

    # 方程
    dXd_dt = cαβ * φ_phot_c - c_resp_d * Xd * 2 ** (0.1 * XT - 2.5)
    dXT_dt = (Uq - Qvent_q + Qrad_q) / c_cap_q
    dXh_dt = (φ_transp_h - φ_vent_h) / c_cap_h
    dXc_dt = (-φ_phot_c + Uc - φ_vent_c + c_resp_c * Xd * 2 ** (0.1 * XT - 2.5)) / c_cap_c

    return [dXd_dt, dXT_dt, dXh_dt, dXc_dt]

# 常数值
constants = [0.544, 2.65 * 10 ** (-7), 4.87 * 10 ** (-7), 30000, 4.1, 4.1, 0, 5.35 * 10 ** (-9), 5.11 * 10 ** (-6), 2.3 * 10 ** (-4), 6.29 * 10 ** (-4), 
             273.15, 0.75 * 10 ** (-4), 53, 3.6 * 10 ** (-3), 9348, 17.4, 239, 8314, 5.2 * 10 ** (-5)]  # 填入所有常数的具体值

# 初始条件
y0 = [0.1, 0.9, 0.5, 0.5]  # 填入初始条件

# 时间范围
t_span = [0, 10]  # 从 t = 0 到 t = 10
t_eval = np.linspace(t_span[0], t_span[1], 100)  # 生成时间点

# 独立变量值
Qvent_q = 1
Qrad_q = 1
Vrad = 1
Uv = 1
Vh = 1
Vc = 1
Uq = 0

# 解方程
sol = solve_ivp(model, t_span, y0, t_eval=t_eval, args=(Qvent_q, Qrad_q, Vrad, Uv, Vh, constants))

# 输出结果
print(sol.y)
    """)

# 社区交流
with tabs[6]:
    st.header("团队交流")
    st.write("在这里提交你的问题或分享你的种植经验：")
    user_input = st.text_area("请输入你的内容")
    if st.button("提交"):
        st.write("感谢你的分享！")

