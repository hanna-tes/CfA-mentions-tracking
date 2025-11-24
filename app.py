import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import gspread
from urllib.parse import urlparse, parse_qs

# --- Configuration for Google Sheets ---
SHEET_NAME = "CfA_mentions_tracker"
WORKSHEET_NAME = "Sheet1"

def get_clean_url(google_url):
    """Extracts the clean URL from a Google redirect link."""
    try:
        parsed_url = urlparse(google_url)
        query_params = parse_qs(parsed_url.query)
        return query_params['url'][0]
    except (KeyError, IndexError, AttributeError):
        return google_url

def categorize_source(url):
    """Categorizes a source based on its URL."""
    url_lower = str(url).lower()
    if any(domain in url_lower for domain in [
        'yahoo.com', 'reuters.com', 'afp.com', 'france24.com',
        'laviesenegalaise.com', 'iol.co.za', 'tuko.co.ke', 'bizcommunity.com'
    ]):
        return 'News Outlet'
    elif 'pressreader.com' in url_lower:
        return 'Digital Paper/Magazine'
    elif any(sm in url_lower for sm in ['twitter.com', 'facebook.com', 'x.com']):
        return 'Social Media'
    elif any(blog in url_lower for blog in ['blogspot.com', 'wordpress.com']):
        return 'Blog'
    else:
        return 'Other'

@st.cache_data(ttl=600)
def load_data_from_google_sheet():
    """Reads and returns cleaned data from Google Sheet."""
    try:
        creds_json = st.secrets["gcp_service_account"]
        client = gspread.service_account_from_dict(creds_json)
        sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error connecting to Google Sheet: {e}")
        return None

def display_dashboard(df_combined):
    # Clean column names
    df_combined.columns = [col.strip().lower() for col in df_combined.columns]

    # Quietly filter out Pesacheck (case-insensitive)
    df_combined = df_combined[df_combined['source'].str.lower() != 'pesacheck']

    # Clean URLs
    df_combined['url'] = df_combined['url'].apply(get_clean_url)

    # Ensure 'daily_update' is datetime and drop invalid rows
    df_combined['daily_update'] = pd.to_datetime(df_combined['daily_update'], errors='coerce')
    df_combined = df_combined.dropna(subset=['daily_update'])

    # Add source category
    df_combined['source_category'] = df_combined['url'].apply(categorize_source)

    # --- High-Level Overview ---
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; border-bottom: 2px solid #5D8AA8; padding-bottom: 10px;">
            <h1 style="color: #5D8AA8;">Dashboard Overview</h1>
        </div>
    """, unsafe_allow_html=True)

    total_mentions = len(df_combined)
    mentions_by_source = df_combined['source'].value_counts()
    top_source = mentions_by_source.index[0] if not mentions_by_source.empty else "N/A"

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"### Total Mentions\n\n**{total_mentions}** external mentions recorded!")
    with col2:
        st.success(f"### Top Source\n\n**{top_source}**")

    # --- All Mentions Table ---
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; border-bottom: 2px solid #5D8AA8; padding-bottom: 10px; margin-top: 30px;">
            <h2 style="color: #5D8AA8;">All Mentions Details</h2>
        </div>
    """, unsafe_allow_html=True)

    # Prepare display dataframe
    display_df = df_combined[['daily_update', 'source', 'title', 'snippet', 'url']].copy()
    display_df = display_df.rename(columns={
        'daily_update': 'Date',
        'source': 'Source',
        'title': 'Title',
        'snippet': 'Snippet',
        'url': 'URL'
    })

    # Sort by date (newest first)
    display_df = display_df.sort_values('Date', ascending=False).reset_index(drop=True)

    # Truncate snippets for readability
    display_df['Snippet'] = display_df['Snippet'].astype(str).str[:200]
    display_df['Snippet'] = display_df['Snippet'].apply(lambda x: x + "..." if len(x) >= 200 else x)

    st.data_editor(
        display_df,
        disabled=True,
        height=500,
        column_config={"URL": st.column_config.LinkColumn("URL")}
    )

    # --- Visualizations ---
    st.markdown("---")
    plt.style.use('dark_background')

    # Mentions by Category
    st.subheader("Mentions by Source Category")
    mentions_by_category = df_combined['source_category'].value_counts()
    fig, ax = plt.subplots(figsize=(10, 6))
    mentions_by_category.plot(kind='bar', color=plt.cm.viridis.colors[:len(mentions_by_category)], ax=ax)
    ax.set_title('Mentions by Source Category', fontsize=16, color='white')
    ax.set_xlabel('Category', fontsize=12, color='white')
    ax.set_ylabel('Number of Mentions', fontsize=12, color='white')
    ax.tick_params(colors='white')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)

    # Top 10 Sources (for clarity)
    st.subheader("Top 10 Mentioning Sources")
    top_sources = mentions_by_source.head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    top_sources.plot(kind='bar', color=plt.cm.Paired.colors[:len(top_sources)], ax=ax)
    ax.set_title('Top 10 Sources by Mentions', fontsize=16, color='white')
    ax.set_xlabel('Source', fontsize=12, color='white')
    ax.set_ylabel('Number of Mentions', fontsize=12, color='white')
    ax.tick_params(colors='white')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(fig)

    # Mentions Over Time
    st.subheader("Mentions Over Time")
    mentions_over_time = df_combined.groupby(df_combined['daily_update'].dt.date).size()
    fig, ax = plt.subplots(figsize=(10, 6))
    mentions_over_time.plot(kind='line', marker='o', linestyle='-', color='#5D8AA8', ax=ax)
    ax.set_title('Mentions Over Time', fontsize=16, color='white')
    ax.set_xlabel('Date', fontsize=12, color='white')
    ax.set_ylabel('Number of Mentions', fontsize=12, color='white')
    ax.grid(True, linestyle='--', alpha=0.6, color='gray')
    ax.tick_params(colors='white')
    plt.tight_layout()
    st.pyplot(fig)

def main():
    st.set_page_config(layout="wide", page_title="Code for Africa Mentions Dashboard")
    st.title("Code for Africa's Work Mentions Tracking Dashboard")
    
    st.sidebar.info("Loading data from Google Sheet...")
    df = load_data_from_google_sheet()
    if df is not None and not df.empty:
        display_dashboard(df)
    else:
        st.warning("No data available. Please check your Google Sheet.")

if __name__ == "__main__":
    main()
