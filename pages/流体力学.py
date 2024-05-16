import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import plotly.graph_objects as go
# 页面配置
st.set_page_config(
    page_title="流体力学仿真介绍",
    page_icon="🌊",
    layout="wide"
)

# 创建标签页
tabs = st.tabs(["基本概念", "数值方法", "应用案例", "交互式仿真"])

# 基本概念
with tabs[0]:
    st.title("流体力学仿真基本概念")
    st.write("""
        流体力学是研究流体运动和相互作用的物理学科，涉及液体和气体的运动、力学性质和应用。常见的流体力学仿真涉及流体流动、热传递、物质输运等方面的模拟和分析。

        一些流体力学的基本概念包括：
        - **流体性质**：包括密度、粘性、压力等。
        - **流体运动描述**：通过速度场和压力场描述流体的运动状态。
        - **流体动力学方程**：如连续性方程、动量方程和能量方程等，用于描述流体的运动规律。

        流体力学仿真是利用数值模拟方法解决流体力学方程的过程，广泛应用于工程、气象、地球科学等领域。
    """)

# 数值方法
with tabs[1]:
    st.title("流体力学仿真数值方法")
    st.write("""
        流体力学仿真常用的数值方法包括有限差分法（FDM）、有限体积法（FVM）和有限元法（FEM）等。

        一些常见的数值方法特点包括：
        - **FDM**：将空间离散为网格，通过中心差分法或向后差分法逼近偏微分方程。
        - **FVM**：将控制体积离散化，利用通量和源项计算控制体积内的平衡。
        - **FEM**：利用有限元网格和基函数逼近偏微分方程的解，具有良好的自适应性和精度。

        这些数值方法可以模拟各种复杂流体现象，如湍流、多相流和热传递等。
    """)

# 应用案例
with tabs[2]:
    st.title("流体力学仿真应用案例")
    st.write("""
        流体力学仿真在各个领域都有重要的应用，包括但不限于：
        - **空气动力学**：飞机机翼设计、风洞实验模拟。
        - **水力学**：水流、河流和水坝的仿真分析。
        - **气象学**：大气环流、气候模拟和风场预测。
        - **生物医学**：血流、呼吸流体力学和药物输送模拟。

        这些应用案例体现了流体力学仿真在解决工程、科学和医学中的重要性和实用性。
    """)

# 交互式仿真
with tabs[3]:
    st.title("交互式流体力学仿真")
    st.write("""
        以下是一个简单的交互式流体力学仿真示例，演示了流经圆柱体的流体流动情况。

        您可以通过调整流体速度和圆柱体直径来观察流场的变化。

    """)

    # 交互式参数调节
    fluid_speed = st.slider("流体速度 (m/s)", min_value=1.0, max_value=10.0, value=5.0, step=1.0)
    cylinder_diameter = st.slider("圆柱体直径 (m)", min_value=0.1, max_value=1.0, value=0.5, step=0.1)

    # 计算流体流动场
    x = np.linspace(-2.0, 2.0, 100)
    y = np.linspace(-2.0, 2.0, 100)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)

    # 计算流体速度场
    U = fluid_speed * (1 - (cylinder_diameter/2)**2 / (R**2 + 1e-6)) * (X / (R + 1e-6))
    V = fluid_speed * (1 - (cylinder_diameter/2)**2 / (R**2 + 1e-6)) * (Y / (R + 1e-6))

    # 创建 Plotly 图表
    fig = go.Figure()

    # 添加流场箭头
    fig.add_trace(go.Scatter(x=X.flatten(), y=Y.flatten(), mode='lines', line=dict(color='blue', width=2)))
    fig.add_trace(go.Scatter(x=X.flatten(), y=Y.flatten(), mode='lines', line=dict(color='blue', width=2)))

    # 设置布局和标题
    fig.update_layout(
        title="流经圆柱体的流体流动",
        xaxis_title="X轴 (m)",
        yaxis_title="Y轴 (m)",
        width=800,
        height=600,
        hovermode='closest'
    )

    # 在 Streamlit 中显示 Plotly 图表
    st.plotly_chart(fig)
