import streamlit as st

# 页面配置
st.set_page_config(
    page_title="智能实时控制算法知识库",
    page_icon="🧠",
    layout="wide"
)

# 创建标签页
tabs = st.tabs(["基本概念", "常见算法", "应用领域","控制绕口令"])

# 基本概念
with tabs[0]:
    st.title("智能实时控制算法基本概念")
    st.write("""
        智能实时控制算法是一类应用于实时决策和控制的算法，通过监测和分析系统状态，实现自动化的决策和调节。以下是一些基本概念：

        - **实时性**：算法需要在实时或近实时条件下处理输入数据和产生输出结果。
        - **智能化**：算法利用机器学习、优化等技术，实现自主学习和优化能力。
        - **控制**：算法用于控制系统的行为，例如调节参数、执行动作等。

        智能实时控制算法在工业自动化、智能交通、机器人控制等领域具有重要应用。
    """)

# 常见算法
with tabs[1]:
    st.title("智能实时控制算法常见类型")
    st.write("""
        智能实时控制算法涵盖多种类型，常见的算法包括但不限于：

        - **PID控制器**：比例-积分-微分控制器，常用于调节系统稳定性和响应速度。
        - **模型预测控制（MPC）**：利用动态模型预测系统未来状态，优化控制策略。
        - **强化学习**：通过试错和奖励机制，优化控制策略，如Q-learning、深度强化学习等。
        - **神经网络控制**：利用神经网络逼近未知系统的动态特性，实现自适应控制。

        这些算法在不同场景下具有独特的优势和适用性，可根据具体需求选择合适的算法。
    """)

# 应用领域
with tabs[2]:
    st.title("智能实时控制算法应用领域")
    st.write("""
        智能实时控制算法在多个领域得到广泛应用：

        - **工业自动化**：用于生产线控制、工艺优化等，提高生产效率和质量。
        - **智能交通**：用于交通信号控制、路径规划等，优化交通流量和安全性。
        - **机器人控制**：用于机器人路径规划、动作控制等，实现自主操作和协作。
        - **智能家居**：用于智能家电控制、能源管理等，提高居住舒适度和能效。
        - **医疗设备**：用于医疗设备监控、患者管理等，提高医疗服务质量和效率。

        这些应用领域体现了智能实时控制算法在推动自动化、智能化和智慧城市发展方面的重要作用。
    """)

with tabs[3]:
    st.title("控制选型绕口令")
    st.write("""
             
            智能控制算法不差香蕉，
            PID、MPC全都行得安宁。
            强化学习如虎添翼，
            神经网络更是无往不胜。

            稳定扬程靠PID支持，
            预测模型MPC解难题。
            奖励惩罚强化学习做，
            神经网络控制最犀利。
             
             """)