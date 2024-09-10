import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
from io import StringIO

# Gist configuration
GIST_ID = "d4ada2ff7bf615924edb4574640607f5"  # numerical data
GIST_URL = f'https://api.github.com/gists/{GIST_ID}'
TOKEN = "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"
HEADERS = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

@st.cache_data(ttl=600)  # Cache the data for 10 minutes
def load_data():
    try:
        response = requests.get(GIST_URL, headers=HEADERS)
        response.raise_for_status()
        gist_data = response.json()
        csv_content = gist_data['files']['log_sensor.csv']['content']
        df = pd.read_csv(StringIO(csv_content))
        df['timestamp'] = pd.to_datetime(df['DateTime'])
        return df
    except Exception as e:
        st.error(f"Error loading data from Gist: {e}")
        return None

def create_plot(df, parameters):
    fig = go.Figure()
    for param in parameters:
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df[param], mode='lines', name=param))
    
    fig.update_layout(
        title="Sensor Data Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Value",
        legend_title="Parameters",
        height=600
    )
    return fig

def main():
    st.title("Plant Factory Sensor Data Visualization")

    df = load_data()
    if df is not None:
        st.write("Data loaded successfully!")

        # Allow user to select date range
        date_range = st.date_input(
            "Select date range",
            value=(df['timestamp'].min().date(), df['timestamp'].max().date()),
            min_value=df['timestamp'].min().date(),
            max_value=df['timestamp'].max().date()
        )

        # Filter data based on selected date range
        start_date, end_date = date_range
        mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
        filtered_df = df.loc[mask]

        # Allow user to select parameters
        all_params = ["Temperature", "Humidity", "CO2", "pH", "WTEMP", "EC", "Wlevel"]
        selected_params = st.multiselect("Select parameters to display", all_params, default=all_params)

        if selected_params:
            fig = create_plot(filtered_df, selected_params)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Please select at least one parameter to display.")

        # Display raw data
        if st.checkbox("Show raw data"):
            st.write(filtered_df)

    else:
        st.error("Failed to load data. Please check your Gist configuration and try again.")

if __name__ == "__main__":
    main()
