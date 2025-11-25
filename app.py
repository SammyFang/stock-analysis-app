import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# --- 設定網頁標題與寬度 ---
st.set_page_config(page_title="股票事件分析器", layout="wide")

st.title("📈 股票事件衝擊分析工具")
st.markdown("上傳 CSV 檔案，輸入事件日期，自動計算前後 5 日的漲跌幅變化。")

# --- 側邊欄：設定區 ---
with st.sidebar:
    st.header("⚙️ 設定")
    event_date_input = st.date_input("選擇事件日期 (Event Date)", value=None)
    st.caption("若不指定日期，將只顯示股價走勢。")

# --- 檔案上傳區 (支援多檔) ---
uploaded_files = st.file_uploader("請上傳股票 CSV 檔 (支援多選)", type=["csv"], accept_multiple_files=True)

def analyze_single_file(file, event_date):
    try:
        #讀取檔案
        df = pd.read_csv(file)
        
        # 資料清洗 (去除逗號，轉數值)
        cols_to_fix = ["Open", "High", "Low", "Close", "Volume"]
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(",", "", regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 日期處理
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors='coerce')
        df = df.dropna(subset=["Date", "Close"]).sort_values("Date")
        
        # 計算報酬率
        df["Pct_Change"] = df["Close"].pct_change() * 100
        
        return df
    except Exception as e:
        st.error(f"讀取檔案 {file.name} 時發生錯誤: {e}")
        return None

# --- 主邏輯 ---
if uploaded_files:
    for uploaded_file in uploaded_files:
        st.divider() # 分隔線
        st.subheader(f"📄 檔案: {uploaded_file.name}")
        
        df = analyze_single_file(uploaded_file, event_date_input)
        
        if df is not None:
            # 建立兩欄佈局 (左邊數據，右邊圖表)
            col1, col2 = st.columns([1, 2])
            
            # --- 事件日數據分析 ---
            before_avg, after_avg = None, None
            valid_event = False
            
            if event_date_input:
                event_ts = pd.Timestamp(event_date_input)
                # 檢查日期是否在範圍內
                if event_ts < df["Date"].min() or event_ts > df["Date"].max():
                    col1.warning(f"⚠️ 事件日 {event_date_input} 超出此股票的數據範圍。")
                else:
                    valid_event = True
                    # 抓取前後數據
                    window = df.loc[(df["Date"] >= event_ts - pd.Timedelta(days=15)) & 
                                    (df["Date"] <= event_ts + pd.Timedelta(days=15))]
                    
                    before = window[window["Date"] < event_ts].tail(5)
                    after = window[window["Date"] > event_ts].head(5)
                    
                    before_avg = before["Pct_Change"].mean()
                    after_avg = after["Pct_Change"].mean()

            # --- 顯示數據 (左欄) ---
            with col1:
                st.dataframe(df.tail(5)[["Date", "Close", "Pct_Change"]], use_container_width=True)
                
                if valid_event:
                    st.markdown("### 📊 事件前後 5 日平均漲跌")
                    metric_col_a, metric_col_b = st.columns(2)
                    metric_col_a.metric("前 5 日平均", f"{before_avg:.2f}%", delta_color="normal")
                    metric_col_b.metric("後 5 日平均", f"{after_avg:.2f}%", 
                                        delta=f"{after_avg:.2f}%", delta_color="inverse")

            # --- 顯示圖表 (右欄) ---
            with col2:
                # 圖表 1: 收盤價
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(df["Date"], df["Close"], label="Close Price", color="#1f77b4")
                if valid_event:
                    ax.axvline(pd.Timestamp(event_date_input), color="red", linestyle="--", label="Event")
                ax.set_title("股價走勢 (Closing Price)")
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)

                # 圖表 2: 漲跌幅
                fig2, ax2 = plt.subplots(figsize=(10, 4))
                colors = ['red' if x < 0 else 'green' for x in df["Pct_Change"]]
                ax2.bar(df["Date"], df["Pct_Change"], color=colors)
                if valid_event:
                    ax2.axvline(pd.Timestamp(event_date_input), color="black", linestyle="--")
                ax2.set_title("每日漲跌幅 (Daily % Change)")
                ax2.set_ylabel("% Change")
                ax2.grid(True, axis='y', alpha=0.3)
                st.pyplot(fig2)

else:
    st.info("👈 請從左側上傳一個或多個 CSV 檔案以開始分析。")