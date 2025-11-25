import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# --- Page Configuration ---
st.set_page_config(page_title="Stock Event Analyzer | Sammy Fang", layout="wide")

# --- Sidebar: Profile & Settings ---
with st.sidebar:
    # 1. Personal Info (Subtle & Professional)
    st.markdown("### 👨‍💻 Developed by")
    st.markdown("**Yung-Sian Fang (Sammy)**")
    st.caption("MBA Candidate @ UC Riverside (Class of 2027)")
    st.caption("Tech Community Organizer | AI & Supply Chain")
    
    st.divider()
    
    # 2. App Settings
    st.header("⚙️ Settings")
    event_date_input = st.date_input("Select Event Date", value=None)
    st.caption("Select a date to analyze price impact 5 days before/after.")

# --- Main Content ---
st.title("📈 Stock Event Impact Analyzer")
st.markdown("""
**Upload your stock data (CSV)** to instantly visualize price trends and analyze market reactions to specific events.
""")

# File Uploader
uploaded_files = st.file_uploader("Upload Stock CSV Files (Support multiple files)", type=["csv"], accept_multiple_files=True)

def analyze_single_file(file, event_date):
    try:
        # Read file
        df = pd.read_csv(file)
        
        # Data Cleaning (Remove commas, convert to float)
        cols_to_fix = ["Open", "High", "Low", "Close", "Volume"]
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", "", regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Date Parsing
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors='coerce')
        df = df.dropna(subset=["Date", "Close"]).sort_values("Date")
        
        # Calculate Daily Returns
        df["Pct_Change"] = df["Close"].pct_change() * 100
        
        return df
    except Exception as e:
        st.error(f"Error reading file {file.name}: {e}")
        return None

# --- Analysis Logic ---
if uploaded_files:
    for uploaded_file in uploaded_files:
        st.divider()
        st.subheader(f"📄 Report: {uploaded_file.name}")
        
        df = analyze_single_file(uploaded_file, event_date_input)
        
        if df is not None:
            # Layout: Metrics on Left, Charts on Right
            col1, col2 = st.columns([1, 2])
            
            # --- Event Analysis ---
            before_avg, after_avg = None, None
            valid_event = False
            
            if event_date_input:
                event_ts = pd.Timestamp(event_date_input)
                
                # Check if date is within range
                if event_ts < df["Date"].min() or event_ts > df["Date"].max():
                    col1.warning(f"⚠️ The event date ({event_date_input}) is out of range for this dataset.")
                else:
                    valid_event = True
                    # Define Window (+/- 15 days for context)
                    window = df.loc[(df["Date"] >= event_ts - pd.Timedelta(days=15)) & 
                                    (df["Date"] <= event_ts + pd.Timedelta(days=15))]
                    
                    # Strict 5-day window calculation
                    before = window[window["Date"] < event_ts].tail(5)
                    after = window[window["Date"] > event_ts].head(5)
                    
                    before_avg = before["Pct_Change"].mean()
                    after_avg = after["Pct_Change"].mean()

            # --- Left Column: Data & Metrics ---
            with col1:
                st.markdown("#### Recent Data")
                st.dataframe(df.tail(5)[["Date", "Close", "Pct_Change"]], use_container_width=True)
                
                if valid_event:
                    st.markdown("#### 📊 5-Day Impact Analysis")
                    st.info("Average Daily Return (%)")
                    metric_col_a, metric_col_b = st.columns(2)
                    
                    # Using 0.00 as default if data is missing (e.g. edge cases)
                    val_before = before_avg if before_avg is not None else 0.0
                    val_after = after_avg if after_avg is not None else 0.0
                    
                    metric_col_a.metric("Before Event", f"{val_before:.2f}%")
                    metric_col_b.metric("After Event", f"{val_after:.2f}%", 
                                        delta=f"{val_after:.2f}%", delta_color="inverse")

            # --- Right Column: Charts ---
            with col2:
                # Chart 1: Closing Price
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(df["Date"], df["Close"], label="Close Price", color="#1f77b4")
                if valid_event:
                    ax.axvline(pd.Timestamp(event_date_input), color="red", linestyle="--", label="Event Date")
                ax.set_title("Stock Price History")
                ax.set_ylabel("Price (USD)")
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)

                # Chart 2: Daily Returns
                fig2, ax2 = plt.subplots(figsize=(10, 4))
                colors = ['red' if x < 0 else 'green' for x in df["Pct_Change"]]
                ax2.bar(df["Date"], df["Pct_Change"], color=colors)
                if valid_event:
                    ax2.axvline(pd.Timestamp(event_date_input), color="black", linestyle="--")
                ax2.set_title("Daily Returns (% Change)")
                ax2.set_ylabel("% Change")
                ax2.grid(True, axis='y', alpha=0.3)
                st.pyplot(fig2)

else:
    st.info("👈 Please upload CSV files from the sidebar to start.")
    
# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey; font-size: 0.8em;'>"
    "© 2025 Yung-Sian Fang (Sammy). All rights reserved.<br>"
    "Designed for financial analysis and visualization."
    "</div>", 
    unsafe_allow_html=True
)
