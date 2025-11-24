import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import gspread
from urllib.parse import urlparse, parse_qs

# --- Configuration for Google Sheets ---
# Name of your Google Sheet
SHEET_NAME = "CfA_mentions_tracker" 
# Name of the worksheet you want to read from
WORKSHEET_NAME = "Sheet1" 

def get_clean_url(google_url):
    """Extracts the clean URL from a Google redirect link."""
    try:
        parsed_url = urlparse(google_url)
        query_params = parse_qs(parsed_url.query)
        return query_params['url'][0]
    except (KeyError, IndexError):
        return google_url

def categorize_source(url):
    """Categorizes a source based on its URL."""
    url_lower = url.lower()
    if ('yahoo.com' in url_lower or 'reuters.com' in url_lower or 
        'afp.com' in url_lower or 'france24.com' in url_lower or
        'laviesenegalaise.com' in url_lower or 'iol.co.za' in url_lower or
        'tuko.co.ke' in url_lower or 'bizcommunity.com' in url_lower):
        return 'News Outlet'
    elif 'pressreader.com' in url_lower:
        return 'Digital Paper/Magazine'
    elif 'twitter.com' in url_lower or 'facebook.com' in url_lower:
        return 'Social Media'
    elif 'blogspot.com' in url_lower or 'wordpress.com' in url_lower:
        return 'Blog'
    # Add more categories as needed
    else:
        return 'Other'

# Function to load data directly from Google Sheets
@st.cache_data(ttl=600)  # Cache data for 10 minutes to avoid hitting API limits
def load_data_from_google_sheet():
    """Reads data from a Google Sheet using a service account credentials from st.secrets."""
    try:
        creds_json = st.secrets["gcp_service_account"]
        client = gspread.service_account_from_dict(creds_json)
        sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error connecting to Google Sheet: {e}. Please check your credentials and sheet name.")
        return None

def display_dashboard(df_combined):
    """
    Displays the dashboard with a more visually appealing design, now focusing on the latest mentions.
    """
    # Clean the column names for easier access
    df_combined.columns = [col.strip().lower() for col in df_combined.columns]

    # Extract clean URLs from the Google redirect links
    df_combined['url'] = df_combined['url'].apply(get_clean_url)

    # Convert 'daily_update' to datetime format
    # Use 'coerce' to handle potential non-date values by setting them to NaT, then drop them
    df_combined['daily_update'] = pd.to_datetime(df_combined['daily_update'], errors='coerce')
    df_combined.dropna(subset=['daily_update'], inplace=True) # Ensure valid dates

    # Add the new source category column
    df_combined['source_category'] = df_combined['url'].apply(categorize_source)

    # --- APPLYING REQUESTED FILTERS AND SORTS ---
    
    # 1. Filter out mentions from 'pesa check'
    # Normalize source
    sources_lower = df_combined['source'].astype(str).str.strip().str.lower()
    df_filtered_all = df_combined[~sources_lower.isin(['pesacheck', 'PesaCheck'])].copy()

    # Sort the DataFrame by 'daily_update' in descending order to easily select the latest
    df_filtered_all.sort_values(by='daily_update', ascending=False, inplace=True)
    
    # --- Sidebar Widget for Latest Mentions ---
    # Determine max value for the slider
    max_mentions = len(df_filtered_all)
    
    st.sidebar.header("📊 Analysis Settings")
    # Add a slider to select the number of latest mentions to analyze
    latest_n = st.sidebar.slider(
        "Select Number of Latest Mentions for Analysis:",
        min_value=1,
        max_value=max_mentions,
        value=min(30, max_mentions), # Default to 30 or the total count if less than 30
        step=1
    )
    
    # 2. Filter the DataFrame to the selected number of latest mentions
    df_latest = df_filtered_all.head(latest_n).copy()
    
    # Re-sort the final display table data to be sequential (oldest to latest)
    # The main table (df_display) should still be sequential
    df_display = df_filtered_all.sort_values(by='daily_update', ascending=True).copy()

    # -------------------------------------------

    # --- High-Level Overview Section ---
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; border-bottom: 2px solid #5D8AA8; padding-bottom: 10px;">
            <h1 style="color: #5D8AA8;">Dashboard Overview</h1>
        </div>
    """, unsafe_allow_html=True)

    # Update the 'Total Mentions' count (based on the filtered data)
    total_mentions = len(df_filtered_all)
    
    # Use the LATEST data for TOP SOURCE calculation
    mentions_by_source_latest = df_latest['source'].value_counts()
    top_source_latest = mentions_by_source_latest.index[0] if not mentions_by_source_latest.empty else "N/A"

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"### Total Mentions\n\n**{total_mentions}** mentions recorded!")
    with col2:
        st.success(f"### Top Source (Latest {latest_n})\n\n**{top_source_latest}** is the top-mentioning source in the latest set.")

    # --- All Mentions Details Section ---
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; border-bottom: 2px solid #5D8AA8; padding-bottom: 10px; margin-top: 30px;">
            <h2 style="color: #5D8AA8;">All Mentions Details (Oldest to Latest)</h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Display all mentions in an interactive table with clickable links
    st.data_editor(
        df_display[['daily_update', 'source', 'title', 'snippet', 'url']].rename(columns={
            'daily_update': 'Date',
            'source': 'Source',
            'title': 'Title',
            'snippet': 'Snippet',
            'url': 'URL'
        }),
        disabled=True,
        height=400,
        column_config={
            "URL": st.column_config.LinkColumn("URL"),
             # Format the date column to be displayed nicely (e.g., YYYY-MM-DD)
            "Date": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD")
        }
    )

    # --- Visualizations Section ---
    st.markdown("---")
    
    # Only calculate and display charts for the LATEST data
    st.markdown(f"**Visualizations based on the latest {latest_n} mentions only.**")

    plt.style.use('dark_background')

    # Chart 1: Mentions by Source Category (using LATEST data)
    mentions_by_category_latest = df_latest['source_category'].value_counts()
    st.subheader(f"Mentions by Source Category (Latest {latest_n})")
    fig, ax = plt.subplots(figsize=(10, 6))
    mentions_by_category_latest.plot(kind='bar', color=plt.cm.viridis.colors, ax=ax)
    ax.set_title(f'Mentions by Source Category (Latest {latest_n})', fontsize=16, color='white')
    ax.set_xlabel('Category', fontsize=12, color='white')
    ax.set_ylabel('Number of Mentions', fontsize=12, color='white')
    ax.tick_params(colors='white')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)

    # Chart 2: Mentions by Source (using LATEST data)
    st.subheader(f"Top Sources by Mention (Latest {latest_n})")
    fig, ax = plt.subplots(figsize=(10, 6))
    mentions_by_source_latest.plot(kind='bar', color=plt.cm.Paired.colors, ax=ax)
    ax.set_title(f'Mentions by Source (Latest {latest_n})', fontsize=16, color='white')
    ax.set_xlabel('Source', fontsize=12, color='white')
    ax.set_ylabel('Number of Mentions', fontsize=12, color='white')
    ax.tick_params(colors='white')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)
    
    # Chart 3: Mentions Over Time (using ALL filtered data to show the full trend)
    st.subheader("Mentions Over Time (Full Trend)")
    mentions_over_time_all = df_filtered_all.groupby('daily_update').size()
    fig, ax = plt.subplots(figsize=(10, 6))
    mentions_over_time_all.plot(kind='line', marker='o', linestyle='-', color='#5D8AA8', ax=ax)
    ax.set_title('Mentions Over Time (All Data)', fontsize=16, color='white')
    ax.set_xlabel('Date', fontsize=12, color='white')
    ax.set_ylabel('Number of Mentions', fontsize=12, color='white')
    ax.grid(True, linestyle='--', alpha=0.6, color='gray')
    ax.tick_params(colors='white')
    plt.tight_layout()
    st.pyplot(fig)

def main():
    st.set_page_config(layout="wide", page_title="Code for Africa's Work Mentions Tracking Dashboard")
    st.title("Code for Africa's Work Mentions Tracking Dashboard")
    
    st.sidebar.info("Loading data directly from your Google Sheet.")
    df = load_data_from_google_sheet()
    if df is not None:
        display_dashboard(df)
    else:
        st.warning("Data could not be loaded from Google Sheet. Please check the credentials and sheet info.")

if __name__ == "__main__":
    main()
