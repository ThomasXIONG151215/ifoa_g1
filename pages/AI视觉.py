import streamlit as st

# 页面配置
st.set_page_config(
    page_title="计算机视觉知识库",
    page_icon="👁️",
    layout="wide"
)

# 创建标签页
tabs = st.tabs(["基础概念", "常见应用", "相关算法"])

# 基础概念
with tabs[0]:
    st.title("计算机视觉基础概念")
    st.write("""
        计算机视觉是一门研究如何使机器“看”的科学和技术领域。以下是计算机视觉的基础概念：

        - **图像获取**：利用摄像头或传感器采集图像数据。
        - **图像预处理**：对图像进行去噪、增强、裁剪等处理，准备用于后续分析。
        - **特征提取**：从图像中提取特定的视觉特征，如边缘、角点、纹理等。
        - **图像识别与分析**：利用机器学习和深度学习技术识别图像中的对象、场景或行为。
        - **目标跟踪**：跟踪目标在图像或视频中的运动轨迹。

        计算机视觉应用涵盖了图像处理、模式识别、机器学习等多个领域，被广泛应用于自动驾驶、医学影像、安防监控等领域。
    """)

# 常见应用
with tabs[1]:
    st.title("计算机视觉常见应用")
    st.write("""
        计算机视觉在各个领域都有重要应用：

        - **自动驾驶**：利用计算机视觉和深度学习技术实现车辆的环境感知和自主导航。
        - **人脸识别**：用于身份验证、安防监控等领域，识别人脸并进行身份匹配。
        - **医学影像分析**：分析医学图像，辅助医生进行疾病诊断和治疗。
        - **智能监控**：用于监控系统，检测异常行为或事件。
        - **工业质检**：检测产品表面缺陷、组装错误等。

        这些应用体现了计算机视觉在实际生活和工业中的重要作用，为自动化和智能化提供支持。
    """)

# 相关算法
with tabs[2]:
    st.title("计算机视觉相关算法")
    st.write("""
        计算机视觉依赖于多种算法和技术：

        - **卷积神经网络（CNN）**：用于图像分类、目标检测等任务的深度学习模型。
        - **特征点检测与描述**：如SIFT、SURF、ORB等算法，用于图像特征提取和匹配。
        - **目标检测与跟踪**：包括YOLO、Faster R-CNN等算法，用于实时目标识别和跟踪。
        - **图像分割**：如语义分割、实例分割等算法，用于将图像分割成不同的区域或对象。

        这些算法为计算机视觉任务提供了有效的解决方案，推动了图像识别和分析技术的发展。
    """)
