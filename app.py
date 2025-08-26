import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import io

# URL for the default dataset (replace with your actual GitHub raw link)
DEFAULT_DATA_URL = "https://raw.githubusercontent.com/hanna-tes/CfA-mentions-tracking/refs/heads/main/news_items%20(1).csv"

def display_dashboard(df_combined):
    """
    Displays the dashboard with a more visually appealing design.
    """
    # Clean the column names for easier access
    df_combined.columns = [col.strip().lower() for col in df_combined.columns]

    # Convert 'daily_update' to datetime format
    df_combined['daily_update'] = pd.to_datetime(df_combined['daily_update'])

    # --- High-Level Overview Section ---
    st.markdown("""
        <div style="text-align: center; border-bottom: 2px solid #00FF00; padding-bottom: 10px;">
            <h1 style="color: #00FF00;">Key Insights</h1>
        </div>
    """, unsafe_allow_html=True)

    total_mentions = len(df_combined)
    mentions_by_source = df_combined['source'].value_counts()
    top_source = mentions_by_source.index[0] if not mentions_by_source.empty else "N/A"

    # Use columns with Streamlit's built-in alert boxes for a better look
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"### Total Mentions\n\n**{total_mentions}** mentions recorded!")
    with col2:
        st.success(f"### Top Source\n\n**{top_source}** is the top-mentioning source.")

    # --- All Mentions Details Section ---
    st.markdown("""
        <div style="text-align: center; border-bottom: 2px solid #00FF00; padding-bottom: 10px; margin-top: 30px;">
            <h2 style="color: #00FF00;">All Mentions Details</h2>
        </div>
    """, unsafe_allow_html=True)

    # Display all mentions in an interactive table
    st.dataframe(df_combined[['daily_update', 'source', 'title', 'snippet', 'url']].rename(columns={
        'daily_update': 'Date',
        'source': 'Source',
        'title': 'Title',
        'snippet': 'Snippet',
        'url': 'URL'
    }), height=400)

    # --- Visualizations Section ---
    st.markdown("""
        <div style="text-align: center; border-bottom: 2px solid #00FF00; padding-bottom: 10px; margin-top: 30px;">
            <h2 style="color: #00FF00;">Data Visualizations</h2>
        </div>
    """, unsafe_allow_html=True)

    # Use a dark background style for a more visually striking look
    plt.style.use('dark_background')

    # Display Mentions by Source plot
    st.subheader("Mentions by Source")
    fig, ax = plt.subplots(figsize=(10, 6))
    mentions_by_source.plot(kind='bar', color=plt.cm.Paired.colors, ax=ax)
    ax.set_title('Mentions by Source', fontsize=16, color='white')
    ax.set_xlabel('Source', fontsize=12, color='white')
    ax.set_ylabel('Number of Mentions', fontsize=12, color='white')
    ax.tick_params(colors='white') # Set tick colors to white for visibility
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)

    # Display Mentions Over Time plot
    st.subheader("Mentions Over Time")
    mentions_over_time = df_combined.groupby('daily_update').size()
    fig, ax = plt.subplots(figsize=(10, 6))
    mentions_over_time.plot(kind='line', marker='o', linestyle='-', color='#00FF00', ax=ax) # Using a bright color for contrast
    ax.set_title('Mentions Over Time', fontsize=16, color='white')
    ax.set_xlabel('Date', fontsize=12, color='white')
    ax.set_ylabel('Number of Mentions', fontsize=12, color='white')
    ax.grid(True, linestyle='--', alpha=0.6, color='gray')
    ax.tick_params(colors='white') # Set tick colors to white
    plt.tight_layout()
    st.pyplot(fig)


def main():
    st.set_page_config(layout="wide")
    st.title("Code for Africa Mentions Dashboard")

    # --- Data Source Selection ---
    st.sidebar.header("Data Source")
    data_source_option = st.sidebar.radio(
        "Choose your data source:",
        ("Use Default Data", "Upload Your Own Dataset")
    )

    st.sidebar.markdown("---")

    if data_source_option == "Use Default Data":
        st.sidebar.info("Using a default dataset from a GitHub repository.")
        st.sidebar.markdown(f"[Raw Data Link]({DEFAULT_DATA_URL})")
        try:
            df = pd.read_csv(DEFAULT_DATA_URL)
            display_dashboard(df)
        except Exception as e:
            st.error(f"Error loading default data: {e}. Please ensure the URL is correct and the file is accessible.")
            st.warning("You may need to upload your own dataset as an alternative.")

    elif data_source_option == "Upload Your Own Dataset":
        st.sidebar.info("Upload one or more CSV files from your local machine.")
        uploaded_files = st.file_uploader(
            "Choose one or more CSV files",
            type="csv",
            accept_multiple_files=True
        )

        if uploaded_files:
            all_dfs = []
            for file in uploaded_files:
                try:
                    df = pd.read_csv(io.StringIO(file.getvalue().decode('utf-8')))
                    all_dfs.append(df)
                except Exception as e:
                    st.error(f"Error reading {file.name}: {e}")
                    return
            df_combined = pd.concat(all_dfs, ignore_index=True)
            display_dashboard(df_combined)
        else:
            st.info("Please upload CSV files to view the dashboard.")

if __name__ == "__main__":
    main()
