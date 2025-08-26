import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def create_dashboard():
    st.title("Code for Africa Mentions Dashboard")

    st.markdown("### Upload Your CSV Files")
    uploaded_files = st.file_uploader(
        "Choose one or more CSV files",
        type="csv",
        accept_multiple_files=True
    )

    if uploaded_files:
        # Create an empty list to store dataframes
        all_dfs = []

        # Read each uploaded file and append its data to the list
        for file in uploaded_files:
            try:
                df = pd.read_csv(file)
                all_dfs.append(df)
            except Exception as e:
                st.error(f"Error reading {file.name}: {e}")
                return

        # Combine all dataframes into a single dataframe
        df_combined = pd.concat(all_dfs, ignore_index=True)

        # Convert 'daily_update' to datetime format
        df_combined['daily_update'] = pd.to_datetime(df_combined['daily_update'])

        # --- Dashboard Layout ---
        st.subheader("High-Level Overview")

        # Calculate total mentions
        total_mentions = len(df_combined)
        st.metric(label="Total Mentions", value=total_mentions)

        # --- Mentions by Source ---
        st.subheader("Mentions by Source")
        mentions_by_source = df_combined['source'].value_counts()
        fig, ax = plt.subplots(figsize=(10, 6))
        mentions_by_source.plot(kind='bar', color='skyblue', ax=ax)
        ax.set_title('Mentions by Source')
        ax.set_xlabel('Source')
        ax.set_ylabel('Number of Mentions')
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)

        # --- Mentions Over Time ---
        st.subheader("Mentions Over Time")
        mentions_over_time = df_combined.groupby('daily_update').size()
        fig, ax = plt.subplots(figsize=(10, 6))
        mentions_over_time.plot(kind='line', marker='o', color='purple', ax=ax)
        ax.set_title('Mentions Over Time')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Mentions')
        ax.grid(True)
        st.pyplot(fig)

        # --- Key Mentions Details ---
        st.subheader("Recent Mentions Details")
        
        # Sort data by date to show the most recent first
        df_sorted = df_combined.sort_values(by='daily_update', ascending=False)
        
        # Display details for each mention
        for index, row in df_sorted.iterrows():
            st.markdown(f"**Source:** {row['source']}")
            st.markdown(f"**Date:** {row['daily_update'].strftime('%B %d, %Y')}")
            st.markdown(f"**Title:** {row['title']}")
            st.markdown(f"**Snippet:** _{row['snippet']}_")
            st.markdown(f"**Link:** [{row['url']}]({row['url']})")
            st.markdown("---") # Add a separator

    else:
        st.info("Please upload CSV files to view the dashboard.")

if __name__ == "__main__":
    create_dashboard()
