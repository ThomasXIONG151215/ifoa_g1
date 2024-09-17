import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests
from datetime import datetime, timedelta

# Gist configuration
GIST_ID = "d4ada2ff7bf615924edb4574640607f5"
GIST_URL = f'https://api.github.com/gists/{GIST_ID}'
TOKEN = "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"
HEADERS = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def fetch_gist_content(file_name):
    response = requests.get(GIST_URL, headers=HEADERS)
    if response.status_code == 200:
        gist_data = response.json()
        return gist_data['files'][file_name]['content']
    else:
        st.error(f"Failed to fetch {file_name}. Status code: {response.status_code}")
        return None

def update_gist_file(file_name, content):
    data = {
        "files": {
            file_name: {
                "content": json.dumps(content, indent=2)
            }
        }
    }
    response = requests.patch(GIST_URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        st.success(f"{file_name} updated successfully!")
    else:
        st.error(f"Failed to update {file_name}. Status code: {response.status_code}")

def load_data():
    content = fetch_gist_content('integral_data.csv')
    if content:
        return pd.read_csv(pd.compat.StringIO(content))
    return None

def load_settings():
    content = fetch_gist_content('settings.json')
    if content:
        return json.loads(content)
    return None

def main():
    st.title("Plant Factory Data Viewer and Settings Editor")

    # Load data and settings
    df = load_data()
    settings = load_settings()

    if df is None or settings is None:
        st.error("Failed to load data or settings. Please check your Gist configuration.")
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
        new_settings['irrigation']['frequency_hours'] = st.number_input("Irrigation Frequency (hours)", 0.1, 24.0, settings['irrigation']['frequency_hours'], 0.1)
        new_settings['irrigation']['duration_minutes'] = st.number_input("Irrigation Duration (minutes)", 1, 60, settings['irrigation']['duration_minutes'])

        # Nutrient solution settings
        st.subheader("Nutrient Solution")
        new_settings['nutrient_solution']['ec_ms_cm'] = st.number_input("EC (mS/cm)", 0.1, 5.0, settings['nutrient_solution']['ec_ms_cm'], 0.1)
        new_settings['nutrient_solution']['ph'] = st.number_input("pH", 0.0, 14.0, settings['nutrient_solution']['ph'], 0.1)

        # Update settings
        if st.button("Update Settings"):
            update_gist_file('settings.json', new_settings)

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
