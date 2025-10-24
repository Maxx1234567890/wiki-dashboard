# app.py
import streamlit as st
import requests
import pandas as pd
import altair as alt # Thư viện vẽ biểu đồ nâng cao hơn

# --- Định nghĩa URL API cho từng Pipe ---
API_EDITS_OVER_TIME = "https://api.tinybird.co/v0/pipes/wiki_events_pipe_edit_time.json"
API_BOT_VS_HUMAN = "https://api.tinybird.co/v0/pipes/wiki_events_pipe_bot_human.json"
API_TOP_SERVERS = "https://api.tinybird.co/v0/pipes/wiki_events_pipe_server.json"
API_TOP_USERS = "https://api.tinybird.co/v0/pipes/wiki_events_pipe_users.json"
API_TOP_PAGES = "https://api.tinybird.co/v0/pipes/wiki_events_pipe_pages.json"

st.set_page_config(layout="wide")
st.title("Dashboard Phân tích Chỉnh sửa Wikipedia 📊")

# --- Hàm tải dữ liệu (giữ nguyên) ---
@st.cache_data(ttl=60)
def get_data(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json().get('data', [])
        # Chuyển đổi cột timestamp thành kiểu datetime
        df = pd.DataFrame(data)
        if 'hour' in df.columns:
             df['hour'] = pd.to_datetime(df['hour'])
        return df
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame()

# --- Nút làm mới ---
if st.button("Làm mới dữ liệu"):
    st.cache_data.clear()
    st.rerun()

# --- Bố cục Dashboard ---
col1, col2 = st.columns(2)

# --- Cột 1 ---
with col1:
    st.subheader("📈 Chỉnh sửa theo thời gian (24h qua)")
    df_time = get_data(API_EDITS_OVER_TIME)
    if not df_time.empty:
        # Dùng Altair để vẽ biểu đồ đường đẹp hơn
        chart_time = alt.Chart(df_time).mark_line().encode(
            x=alt.X('hour', title='Giờ'),
            y=alt.Y('total_edits', title='Số lượng chỉnh sửa')
        ).properties(
             height=300
        )
        st.altair_chart(chart_time, use_container_width=True)
    else:
        st.warning("Không có dữ liệu.")

    st.subheader("🌐 Top 10 Ngôn ngữ (Server)")
    df_servers = get_data(API_TOP_SERVERS)
    if not df_servers.empty:
        st.bar_chart(df_servers.set_index('server_name'))
    else:
        st.warning("Không có dữ liệu.")

    st.subheader("📄 Top 10 Trang được sửa nhiều nhất")
    df_pages = get_data(API_TOP_PAGES)
    if not df_pages.empty:
        st.dataframe(df_pages)
    else:
        st.warning("Không có dữ liệu.")


# --- Cột 2 ---
with col2:
    st.subheader("🤖 Bot vs Người thật")
    df_bot_human = get_data(API_BOT_VS_HUMAN)
    if not df_bot_human.empty:
         # Map True/False thành tên dễ đọc
        df_bot_human['is_bot_label'] = df_bot_human['is_bot'].map({True: 'Bot', False: 'Người thật'})
        chart_bot_human = alt.Chart(df_bot_human).mark_arc(inner_radius=50).encode(
            theta=alt.Theta(field="total_edits", type="quantitative"),
            color=alt.Color(field="is_bot_label", type="nominal", title="Loại"),
            tooltip=['is_bot_label', 'total_edits']
        ).properties(
             title='Phân bố Bot vs Người', height=300
        )
        st.altair_chart(chart_bot_human, use_container_width=True)
    else:
        st.warning("Không có dữ liệu.")

    st.subheader("👥 Top 10 Người dùng/Bot tích cực")
    df_users = get_data(API_TOP_USERS)
    if not df_users.empty:
        st.dataframe(df_users)
    else:
        st.warning("Không có dữ liệu.")
