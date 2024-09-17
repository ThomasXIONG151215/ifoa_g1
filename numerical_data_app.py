import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta
import os
from st_files_connection import FilesConnection

def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        st.error(f"File not found: {file_path}")
        return None

def load_settings(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        st.error(f"File not found: {file_path}")
        return None

def save_settings(file_path, settings):
    with open(file_path, 'w') as f:
        json.dump(settings, f, indent=2)
    st.success("Settings updated successfully!")

def main():
    st.title("Plant Factory Data Viewer and Settings Editor")

    conn = st.connection('s3', type=FilesConnection)
    # File paths
    data_file = 'integral_data.csv'
    settings_file = 'settings.json'

    # Load data and settings
    df = conn.read("ifoag1/integral_data.csv", input_format="csv", ttl=600) #load_data(data_file)
    settings = conn.read("ifoag1/settings.json", input_format="json", ttl=600)#load_settings(settings_file)

    if df is None or settings is None:
        st.error("Failed to load data or settings. Please check your file paths.")
        return

    # Settings Editor
    st.header("Settings Editor")
    with st.expander("Edit Settings"):
        new_settings = settings.copy()
        
        # Lighting settings
        st.subheader("Lighting")
        new_settings['lighting']['duration_hours'] = st.slider("Light Duration (hours)", 1, 24, settings['lighting']['duration_hours'])
        new_settings['lighting']['dark_period_hours'] = st.slider("Dark Period (hours)", 0, 24, settings['lighting']['dark_period_hours'])
        new_settings['lighting']['intensity_percentage'] = st.slider("Light Intensity (%)", 0, 100, settings['lighting']['intensity_percentage'])

        # Strategy
        new_settings['strategy'] = st.selectbox("Strategy", ["步步为营", "全面打击", "火力覆盖"], index=["步步为营", "全面打击", "火力覆盖"].index(settings['strategy']))

        # Environment settings
        st.subheader("Environment")
        for period in ['light_period', 'dark_period']:
            st.write(f"{period.replace('_', ' ').title()}")
            new_settings['environment'][period]['temperature_celsius'] = st.slider(f"Temperature (°C) - {period}", 0, 40, settings['environment'][period]['temperature_celsius'])
            new_settings['environment'][period]['humidity_percentage'] = st.slider(f"Humidity (%) - {period}", 0, 100, settings['environment'][period]['humidity_percentage'])
            new_settings['environment'][period]['co2_ppm'] = st.slider(f"CO2 (ppm) - {period}", 0, 2000, settings['environment'][period]['co2_ppm'])

        # Irrigation settings
        st.subheader("Irrigation")
        new_settings['irrigation']['frequency_hours'] = st.number_input("Irrigation Frequency (hours)", 0.1, 24.0, float(settings['irrigation']['frequency_hours']), 0.1)
        new_settings['irrigation']['duration_minutes'] = st.number_input("Irrigation Duration (minutes)", 1, 60, int(settings['irrigation']['duration_minutes']), 1)
        # Nutrient solution settings
        st.subheader("Nutrient Solution")
        new_settings['nutrient_solution']['ec_ms_cm'] = st.number_input("EC (mS/cm)", 0.1, 5.0, settings['nutrient_solution']['ec_ms_cm'], 0.1)
        new_settings['nutrient_solution']['ph'] = st.number_input("pH", 0.0, 14.0, settings['nutrient_solution']['ph'], 0.1)

        # Update settings
        if st.button("Update Settings"):
            save_settings(settings_file, new_settings)

    # Data Viewer
    st.header("Data Viewer")
    
    # Convert DateTime column to datetime
    df['DateTime'] = pd.to_datetime(df['DateTime_y'])

    # Time range selector
    date_range = st.date_input(
        "Select date range",
        [df['DateTime'].min().date(), df['DateTime'].max().date()]
    )
    start_date, end_date = date_range
    mask = (df['DateTime'].dt.date >= start_date) & (df['DateTime'].dt.date <= end_date)
    filtered_df = df.loc[mask]

    # Column selector
    data_columns = ['Temperature', 'Humidity', 'CO2PPM', 'pH', 'WTEMP', 'EC', 'Wlevel']
    selected_columns = st.multiselect("Select columns to display", data_columns, default=['Temperature', 'Humidity', 'CO2PPM'])

    if selected_columns:
        fig = px.line(filtered_df, x='DateTime', y=selected_columns, title='Plant Factory Environmental Data')
        fig.update_layout(legend_title_text='Parameters')
        st.plotly_chart(fig)
    else:
        st.warning("Please select at least one column to display.")

if __name__ == "__main__":
    main()
