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
        st.error(f"Error loading data from S3: {str(e)}")
        return None

def load_settings(conn):
    try:
        return conn.read("ifoag1/settings.json", input_format="json", ttl=600)
    except Exception as e:
        st.error(f"Error loading settings from S3: {str(e)}")
        return None

def save_settings(conn, settings):
    try:
        conn.write("ifoag1/settings.json", json.dumps(settings, indent=2))
        st.success("Settings updated successfully!")
    except Exception as e:
        st.error(f"Failed to update settings: {str(e)}")

def settings_editor(conn, settings):
    new_settings = settings.copy()
    
    st.header("Settings Editor")
    
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
    new_settings['nutrient_solution']['ec_ms_cm'] = st.number_input("EC (mS/cm)", 0.1, 5.0, float(settings['nutrient_solution']['ec_ms_cm']), 0.1)
    new_settings['nutrient_solution']['ph'] = st.number_input("pH", 0.0, 14.0, float(settings['nutrient_solution']['ph']), 0.1)

    # Update settings
    if st.button("Update Settings"):
        save_settings(conn, new_settings)
        
def data_viewer(df):
    st.header("Data Viewer")
    
    if df is None or df.empty:
        st.warning("No data available for visualization.")
        return

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

    # Group columns by types
    column_groups = {
        'Temperature': ['Temperature', 'Temperature1', 'Temperature2', 'Temperature3', 'WTEMP'],
        'Humidity': ['Humidity', 'Humidity1', 'Humidity2', 'Humidity3'],
        'CO2': ['CO2PPM', 'CO2M', 'CO2PPM4', 'CO2M4'],
        'Water Quality': ['pH', 'EC'],
        'Water Level': ['Wlevel']
    }

    # Create plots for each group
    for group, columns in column_groups.items():
        fig = go.Figure()
        for column in columns:
            if column in filtered_df.columns:
                fig.add_trace(go.Scatter(x=filtered_df['DateTime'], y=filtered_df[column], mode='lines', name=column))
        
        if len(fig.data) > 0:  # Only display the plot if it has data
            fig.update_layout(
                title=f'{group} Data',
                xaxis_title='DateTime',
                yaxis_title='Value',
                legend_title='Sensors',
                height=600,  # Increase height for better visibility
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

    # Add a summary statistics table
    st.subheader("Summary Statistics")
    summary_df = filtered_df[list(sum(column_groups.values(), []))].describe()
    st.dataframe(summary_df)

    # Add a data download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name="plant_factory_data.csv",
        mime="text/csv",
    )

def main():
    st.title("Plant Factory Data Viewer and Settings Editor")

    conn = st.connection('s3', type=FilesConnection)

    # Load data and settings
    df = load_data(conn)
    settings = load_settings(conn)

    if settings is None:
        st.error("Failed to load settings. Please check your S3 configuration.")
        return

    # Create tabs for Settings Editor and Data Viewer
    tab1, tab2 = st.tabs(["Settings Editor", "Data Viewer"])

    with tab1:
        settings_editor(conn, settings)

    with tab2:
        data_viewer(df)

if __name__ == "__main__":
    main()
