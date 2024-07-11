import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import cv2
import time
import pickle
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Define a class to hold the state of each system and the historical data
class SystemState:
    def __init__(self):
        self.ro_filter_system = False
        self.uv_sterilizer = False
        self.co2_cylinder = False
        self.ro_activation_indices = []
        self.uv_activation_indices = []
        self.co2_activation_indices = []
        self.historical_data = self.generate_fake_data()

    def generate_fake_data(self):
        dates = pd.date_range(datetime.now() - timedelta(days=30), periods=30, freq='D')
        data = {
            'Date': dates,
            'Temperature (°C)': np.random.uniform(20, 30, size=30),
            'Humidity (%)': np.random.uniform(40, 60, size=30),
            'CO2 (ppm)': np.random.uniform(300, 500, size=30),
            'PM2.5 (µg/m³)': np.random.uniform(0, 50, size=30),
            'VOC (ppm)': np.random.uniform(0, 1, size=30),
            'LED PPFD (µmol/m²/s)': np.random.uniform(100, 400, size=30),
            'Water pH': np.random.uniform(5.5, 6.5, size=30),
            'EC (dS/m)': np.random.uniform(1.0, 2.5, size=30),
            'Energy Consumption (kWh)': np.random.uniform(100, 500, size=30)
        }
        return pd.DataFrame(data)

    def update_historical_data(self):
        new_entry = {
            'Date': datetime.now(),
            'Temperature (°C)': np.random.uniform(20, 30),
            'Humidity (%)': np.random.uniform(40, 60),
            'CO2 (ppm)': np.random.uniform(300, 500),
            'PM2.5 (µg/m³)': np.random.uniform(0, 50),
            'VOC (ppm)': np.random.uniform(0, 1),
            'LED PPFD (µmol/m²/s)': np.random.uniform(100, 400),
            'Water pH': np.random.uniform(5.5, 6.5),
            'EC (dS/m)': np.random.uniform(1.0, 2.5),
            'Energy Consumption (kWh)': np.random.uniform(100, 500)
        }
        self.historical_data = self.historical_data.append(new_entry, ignore_index=True)

    def check_for_faults(self, control_state, time_steps=10):
        data = self.historical_data
        faults = []
        
        # Check RO and UV faults
        if control_state.ro_filter_system:
            self.ro_activation_indices.append(len(data) - 1)
            if len(self.ro_activation_indices) >= 2:
                for start_idx in self.ro_activation_indices[:-1]:
                    end_idx = start_idx + time_steps
                    if end_idx < len(data) and data['EC (dS/m)'].iloc[start_idx:end_idx].diff().sum() == 0:
                        faults.append("RO system not affecting water quality (EC)")

        if control_state.uv_sterilizer:
            self.uv_activation_indices.append(len(data) - 1)
            if len(self.uv_activation_indices) >= 2:
                for start_idx in self.uv_activation_indices[:-1]:
                    end_idx = start_idx + time_steps
                    if end_idx < len(data) and data['EC (dS/m)'].iloc[start_idx:end_idx].diff().sum() == 0:
                        faults.append("UV system not affecting water quality (EC)")

        # Check CO2 cylinder faults
        if control_state.co2_cylinder:
            self.co2_activation_indices.append(len(data) - 1)
            if len(self.co2_activation_indices) >= 2:
                for start_idx in self.co2_activation_indices[:-1]:
                    end_idx = start_idx + time_steps
                    if end_idx < len(data) and data['CO2 (ppm)'].iloc[start_idx:end_idx].max() < 0.8 * control_state.target_co2:
                        faults.append("CO2 cylinder might be empty")
        
        return faults



def load_secret_data(filename='secret.pkl'):
    """Load the secret data from a pickle file."""
    with open(filename, 'rb') as f:
        return pickle.load(f)

def hash_password(password):
    """Create a SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()

def auth():
    custom_color_rgb = "rgb(138, 43, 226)"  # 定义自定义 RGB 颜色
    title_html = f'欢迎来到 <span style="color: {custom_color_rgb};">室墨司源</span>'

    st.title('欢迎来到 :green[室墨司源]')

    with st.container(border=True):
        
        # Load the secret data
        try:
            secret_data = load_secret_data()
        except FileNotFoundError:
            st.error("Secret data file not found. Please run generate_secret_key.py first.")
            return
         
        username = st.text_input('用户名')
        password = st.text_input('密码', type='password')
        
        if st.button("Login"):
            
            if username in secret_data['users'] and hash_password(password) == secret_data['users'][username]:
                st.success("Login successful!")
                st.session_state['authenticated'] = True
                st.experimental_rerun()
            else:
                st.error("Login failed. Incorrect username or password.")

# Define thresholds for fault detection
thresholds = {
    'Temperature (°C)': (18, 32),
    'Humidity (%)': (35, 65),
    'CO2 (ppm)': (280, 520),
    'PM2.5 (µg/m³)': (0, 45),
    'VOC (ppm)': (0, 0.9),
    'LED PPFD (µmol/m²/s)': (80, 450),
    'Water pH': (5.0, 7.0),
    'EC (dS/m)': (0.8, 2.8),
    'Energy Consumption (kWh)': (50, 550)
}

# Function to check for faults
def check_for_faults(data, control_state):
    faults = []
    for param, (low, high) in thresholds.items():
        if data[param].iloc[-1] < low or data[param].iloc[-1] > high:
            faults.append(param)
    
    # Check RO and UV fault
    if control_state.ro_filter_system or control_state.uv_sterilizer:
        recent_ec_changes = data['EC (dS/m)'].diff().tail(10)
        if recent_ec_changes.sum() == 0:
            faults.append("RO or UV system not affecting water quality (EC)")

    # Check CO2 cylinder fault
    if control_state.co2_cylinder:
        recent_co2_levels = data['CO2 (ppm)'].tail(10)
        if recent_co2_levels.max() < 0.8 * control_state.target_co2:
            faults.append("CO2 cylinder might be empty")
    
    return faults

# Function to send alert
def send_alert(faults):
    sender_email = "your_email@example.com"
    receiver_email = "receiver_email@example.com"
    password = "your_email_password"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Plant Factory Alert"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = f"The following parameters are out of range:\n\n{', '.join(faults)}"
    part = MIMEText(text, "plain")
    message.attach(part)

    with smtplib.SMTP_SSL("smtp.example.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

# Function to monitor data
# Function to monitor data
def monitor_data(state):
    faults = state.check_for_faults(state)
    if faults:
        st.error(f"Fault Detected: {', '.join(faults)}")
        # Send an email alert
        send_alert(faults)
    else:
        st.success("All parameters are within normal range.")


# Function to update historical data with new entry
def update_historical_data(state):
    new_entry = {
        'Date': datetime.now(),
        'Temperature (°C)': np.random.uniform(20, 30),
        'Humidity (%)': np.random.uniform(40, 60),
        'CO2 (ppm)': np.random.uniform(300, 500),
        'PM2.5 (µg/m³)': np.random.uniform(0, 50),
        'VOC (ppm)': np.random.uniform(0, 1),
        'LED PPFD (µmol/m²/s)': np.random.uniform(100, 400),
        'Water pH': np.random.uniform(5.5, 6.5),
        'EC (dS/m)': np.random.uniform(1.0, 2.5),
        'Energy Consumption (kWh)': np.random.uniform(100, 500)
    }
    state.historical_data = state.historical_data.append(new_entry, ignore_index=True)

def main():
    if 'system_state' not in st.session_state:
        st.session_state.system_state = SystemState()

    state = st.session_state.system_state

    # Generate fake data
    historical_data = state.historical_data

    # Inject custom CSS to center tabs
    st.markdown("""
        <style>
        /* Target only the stTabs container to center the tabs */
        div[data-testid="stHorizontalBlock"] {
            display: flex;
            justify-content: center;
        }
        </style>
        """, unsafe_allow_html=True)

    # Sidebar with logo and introduction
    st.sidebar.image("logo.png", use_column_width=True)
    st.sidebar.title("Plant Factory Management")
    st.sidebar.markdown("""
    Manage your plant factory efficiently with this app. Monitor key parameters, control the environment manually or automatically, and view live camera feeds.
    """)

    # Initialize session state for control mode if it doesn't exist
    if 'control_mode' not in st.session_state:
        st.session_state.control_mode = "Manual"

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Monitor Data", "Control", "Camera Feed"])

    # Monitor Data Tab
    with tab1:
        st.header("Historical Data Monitoring")
        
        # Sidebar selection for parameters to display
        parameters = st.sidebar.multiselect(
            "Select parameters to display:",
            ['Temperature (°C)', 'Humidity (%)', 'CO2 (ppm)', 'PM2.5 (µg/m³)', 
            'VOC (ppm)', 'LED PPFD (µmol/m²/s)', 'Water pH', 'EC (dS/m)', 'Energy Consumption (kWh)'],
            default=['Temperature (°C)', 'Humidity (%)']
        )

        # Plotly figures
        for param in parameters:
            fig = px.line(historical_data, x='Date', y=param, title=f'{param} Over Time')
            st.plotly_chart(fig)

        # Monitor current data for faults
        monitor_data(state)

    # Control Tab
    with tab2:
        st.header("Control Settings")

        # Use session state for control mode
        st.session_state.control_mode = st.sidebar.radio("Select Control Mode", ["Manual", "Semi-Automate", "Full-Automate"])
        
        st.info(f"Current Control Mode: {st.session_state.control_mode}")

        if st.session_state.control_mode == "Manual":
            st.subheader("Manual Control")
            st.subheader("LED Light Settings")
            ppfd = st.slider("Set LED PPFD (µmol/m²/s)", 0, 500, 300)
            light_duration = st.slider("Set Light Duration (hours)", 0, 24, 16)
            
            st.subheader("HVAC Settings")
            hvac_mode = st.selectbox("Select HVAC Mode", ["Off", "Cooling", "Heating", "Ventilation"])
            flow_rate = st.slider("Set Flow Rate (%)", 0, 100, 50)
            fresh_air_flow_rate = st.slider("Set Fresh Air Flow Rate (%)", 0, 100, 30)
            temperature = st.slider("Set Temperature (°C)", 10, 35, 22)
            humidity = st.slider("Set Humidity (%)", 10, 90, 60)
            
            st.subheader("Water and Fertilizer Machine Settings")
            water_ph = st.slider("Set Water pH", 4.0, 8.0, 6.0)
            ec = st.slider("Set EC (dS/m)", 0.5, 3.0, 1.5)
            nutrient_a = st.slider("Set Nutrient A (%)", 0, 100, 30)
            nutrient_b = st.slider("Set Nutrient B (%)", 0, 100, 30)
            nutrient_c = st.slider("Set Nutrient C (%)", 0, 100, 40)
            
            st.subheader("Additional Device Controls")
            state.ro_filter_system = st.checkbox("RO Filter System", value=False)
            state.uv_sterilizer = st.checkbox("UV Sterilizer", value=False)
            state.co2_cylinder = st.checkbox("CO2 Cylinder", value=False)
            
            if st.button("Apply Settings"):
                state.update_historical_data()
                st.success("Settings applied successfully!")

        elif st.session_state.control_mode == "Semi-Automate":
            st.subheader("Semi-Automate Mode")
            target_temp = st.slider("Target Temperature (°C)", 10, 35, 22)
            state.target_co2 = st.slider("Target CO2 (ppm)", 300, 1500, 400)
            target_ppfd = st.slider("Target LED PPFD (µmol/m²/s)", 0, 500, 300)
            target_ph = st.slider("Target pH", 4.0, 8.0, 6.0)
            target_ec = st.slider("Target EC (dS/m)", 0.5, 3.0, 1.5)
            target_pm = st.slider("Target PM2.5 (µg/m³)", 0, 100, 25)
            
            if st.button("Run Semi-Automate Mode"):
                state.update_historical_data()
                st.success("Semi-automate mode activated!")

        elif st.session_state.control_mode == "Full-Automate":
            st.subheader("Full-Automate Mode")
            growth_stage = st.selectbox("Select Plant Growth Stage", ["Seedling", "Vegetative", "Flowering"])
            
            if st.button("Run Full-Automate Mode"):
                state.update_historical_data()
                st.success("Full-automate mode activated!")



    # Camera Feed Tab
    with tab3:
        st.header("Camera Feed")

        # Initialize session state for camera status if it doesn't exist
        if 'camera_on' not in st.session_state:
            st.session_state.camera_on = False

        # Sidebar selection for camera number
        camera_number = st.sidebar.selectbox("Select Camera Number", [0, 1, 2, 3])

        # Button to toggle camera on/off
        if st.button("Toggle Camera On/Off"):
            st.session_state.camera_on = not st.session_state.camera_on

        # Display current camera status
        st.write(f"Camera is currently {'ON' if st.session_state.camera_on else 'OFF'}")

        # Camera feed
        if st.session_state.camera_on:
            # Access the webcam
            cap = cv2.VideoCapture(camera_number)

            if not cap.isOpened():
                st.error("Error: Could not open camera.")
            else:
                # Display live video feed
                stframe = st.empty()
                while st.session_state.camera_on:
                    ret, frame = cap.read()
                    if not ret:
                        st.error("Error: Could not read frame.")
                        break
                    
                    # Convert frame to RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Display frame
                    stframe.image(frame)

                # Release the webcam when the camera is turned off
                cap.release()
        else:
            st.info("Camera is turned off. Click the button above to turn it on.")

def app():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if st.session_state['authenticated']:
        main()
    else:
        auth()

if __name__ == "__main__":
    app()
