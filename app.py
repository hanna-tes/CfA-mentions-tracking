import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import io

# URL for the default dataset (replace with your actual GitHub raw link)
DEFAULT_DATA_URL = "https://raw.githubusercontent.com/username/repository/main/news_items.csv"

def create_dashboard():
    # Set Streamlit page configuration for a wider layout
    st.set_page_config(layout="wide")

    st.title("Code for Africa Mentions Dashboard")

    # --- Data Selection Section ---
    st.sidebar.header("Data Source")
    data_source_option = st.sidebar.radio(
        "Choose your data source:",
        ("Use Default Data", "Upload Your Own Dataset")
    )

    df_combined = pd.DataFrame()

    if data_source_option == "Use Default Data":
        st.info("Using a default dataset from a GitHub repository.")
        st.markdown(f"[Raw Data Link]({DEFAULT_DATA_URL})")
        try:
            df = pd.read_csv(DEFAULT_DATA_URL)
            df_combined = df
        except Exception as e:
            st.error(f"Error loading default data: {e}")
            return
    else:
        st.markdown("### Upload Your CSV Files")
        uploaded_files = st.file_uploader(
            "Choose one or more CSV files",
            type="csv",
            accept_multiple_files=True
        )

        if not uploaded_files:
            st.info("Please upload CSV files to view the dashboard.")
            return

        all_dfs = []
        for file in uploaded_files:
            try:
                # Use io.StringIO to read the file in memory
                df = pd.read_csv(io.StringIO(file.getvalue().decode('utf-8')))
                all_dfs.append(df)
            except Exception as e:
                st.error(f"Error reading {file.name}: {e}")
                return
        df_combined = pd.concat(all_dfs, ignore_index=True)

    if not df_combined.empty:
        # Clean the column names for easier access
        df_combined.columns = [col.strip().lower() for col in df_combined.columns]

        # Convert 'daily_update' to datetime format
        df_combined['daily_update'] = pd.to_datetime(df_combined['daily_update'])

        # --- High-Level Overview Section ---
        st.markdown("---")
        st.markdown("<h2 style='text-align: center;'>Overview</h2>", unsafe_allow_html=True)
        st.markdown("---")

        total_mentions = len(df_combined)
        mentions_by_source = df_combined['source'].value_counts()
        top_source = mentions_by_source.index[0] if not mentions_by_source.empty else "N/A"

        # Use columns to align the metrics neatly
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Total Mentions**")
            st.markdown(f"<p style='font-size: 3rem;'>{total_mentions}</p>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"**Top Source**")
            st.markdown(f"<p style='font-size: 3rem;'>{top_source}</p>", unsafe_allow_html=True)

        # --- Visualizations Section ---
        st.markdown("---")
        st.markdown("<h2 style='text-align: center;'>Data Visualizations</h2>", unsafe_allow_html=True)
        st.markdown("---")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("Mentions by Source")
            # Create a more visually appealing bar chart
            fig, ax = plt.subplots(figsize=(8, 5))
            mentions_by_source.plot(kind='bar', color=plt.cm.Paired.colors, ax=ax)
            ax.set_title('Mentions by Source', fontsize=16)
            ax.set_xlabel('Source', fontsize=12)
            ax.set_ylabel('Number of Mentions', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            st.pyplot(fig)

        with chart_col2:
            st.subheader("Mentions Over Time")
            # Create a more visually appealing line chart
            mentions_over_time = df_combined.groupby('daily_update').size()
            fig, ax = plt.subplots(figsize=(8, 5))
            mentions_over_time.plot(kind='line', marker='o', linestyle='-', color='#4B0082', ax=ax)
            ax.set_title('Mentions Over Time', fontsize=16)
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Number of Mentions', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            st.pyplot(fig)

        # --- Raw Data and Details Section ---
        st.markdown("---")
        st.markdown("<h2 style='text-align: center;'>Recent Mentions Details</h2>", unsafe_allow_html=True)
        st.markdown("---")

        # Sort data by date to show the most recent first
        df_sorted = df_combined.sort_values(by='daily_update', ascending=False)

        # Use a container for the details to make them visually grouped
        with st.container(border=True):
            for index, row in df_sorted.iterrows():
                st.markdown(f"**Source:** {row['source']} | **Date:** {row['daily_update'].strftime('%B %d, %Y')}")
                st.markdown(f"**Title:** [{row['title']}]({row['url']})")
                st.markdown(f"**Snippet:** _{row['snippet']}_")
                st.markdown("---")  # Add a separator

if __name__ == "__main__":
    create_dashboard()
