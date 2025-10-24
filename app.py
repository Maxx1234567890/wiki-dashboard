# app.py
import streamlit as st
import requests
import pandas as pd
import altair as alt

# --- ĐỊNH NGHĨA 5 URL API CỦA BẠN ---
API_EDITS_OVER_TIME = "https://api.tinybird.co/v0/pipes/wiki_events_pipe_edit_time.json"
API_BOT_VS_HUMAN = "https://api.tinybird.co/v0/pipes/wiki_events_pipe_bot_human.json"
API_TOP_SERVERS = "https://api.tinybird.co/v0/pipes/wiki_events_pipe_server.json"
API_TOP_USERS = "https://api.tinybird.co/v0/pipes/wiki_events_pipe_users.json"
API_TOP_PAGES = "https://api.tinybird.co/v0/pipes/wiki_events_pipe_pages.json"

st.set_page_config(layout="wide")
st.title("Dashboard Phân tích Chỉnh sửa Wikipedia 📊")

# --- HÀM TẢI DỮ LIỆU ---
# Hàm này sẽ được gọi 5 lần, nhưng chỉ dùng 1 token
@st.cache_data(ttl=60)
def get_data(api_url):
    try:
        # 1. Lấy token bí mật từ Streamlit Secrets
        token = st.secrets["TINYBIRD_TOKEN"]
        
        # 2. Tạo headers để xác thực
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Thêm headers vào yêu cầu GET
        response = requests.get(api_url, headers=headers) 
        response.raise_for_status() # Báo lỗi nếu API hỏng (403, 404...)
        
        data = response.json().get('data', [])
        df = pd.DataFrame(data)
        if 'hour' in df.columns:
             df['hour'] = pd.to_datetime(df['hour'])
        return df
    
    except KeyError:
        st.error("Lỗi: TINYBIRD_TOKEN chưa được thiết lập trong Streamlit Secrets.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi tải dữ liệu: {e}")
        return pd.DataFrame()

# --- Nút làm mới ---
if st.button("Làm mới dữ liệu"):
    st.cache_data.clear()
    st.rerun()

# --- BỐ CỤC DASHBOARD ---
col1, col2 = st.columns(2)

# --- Cột 1 ---
with col1:
    st.subheader("📈 Chỉnh sửa theo thời gian (24h qua)")
    df_time = get_data(API_EDITS_OVER_TIME) # <-- Gọi hàm
    if not df_time.empty:
        chart_time = alt.Chart(df_time).mark_line().encode(
            x=alt.X('hour', title='Giờ'),
            y=alt.Y('total_edits', title='Số lượng chỉnh sửa')
        ).properties(height=300)
        st.altair_chart(chart_time, use_container_width=True)
    else:
        st.warning("Không có dữ liệu.")

    st.subheader("🌐 Top 10 Ngôn ngữ (Server)")
    df_servers = get_data(API_TOP_SERVERS) # <-- Gọi hàm
    if not df_servers.empty:
        st.bar_chart(df_servers.set_index('server_name'))
    else:
        st.warning("Không có dữ liệu.")

    st.subheader("📄 Top 10 Trang được sửa nhiều nhất")
    df_pages = get_data(API_TOP_PAGES) # <-- Gọi hàm
    if not df_pages.empty:
        st.dataframe(df_pages)
    else:
        st.warning("Không có dữ liệu.")

# --- Cột 2 ---
with col2:
    st.subheader("🤖 Bot vs Người thật")
    df_bot_human = get_data(API_BOT_VS_HUMAN) # Gọi API

    # ----- THÊM PHẦN KIỂM TRA DỮ LIỆU -----
    st.write("Dữ liệu Bot vs Người thật:")
    if not df_bot_human.empty:
        st.dataframe(df_bot_human)
        st.write("Kiểu dữ liệu:")
        st.write(df_bot_human.dtypes)
    else:
        st.warning("Không có dữ liệu Bot vs Người thật.")
    # ----- KẾT THÚC KIỂM TRA -----

    if not df_bot_human.empty:
        try:
            # Đảm bảo total_edits là số và không có null (thay bằng 0 nếu null)
            df_bot_human['total_edits'] = pd.to_numeric(df_bot_human['total_edits'], errors='coerce').fillna(0)

            # Map True/False thành tên dễ đọc
            df_bot_human['is_bot_label'] = df_bot_human['is_bot'].map({True: 'Bot', False: 'Người thật'})

            # Tạo biểu đồ tròn (donut chart)
            chart_bot_human = alt.Chart(df_bot_human).mark_arc(inner_radius=50).encode(
                # Theta là góc, dùng cột total_edits (đã được tổng hợp bởi Tinybird)
                theta=alt.Theta(field="total_edits", type="quantitative"),
                # Color là màu sắc, dùng cột is_bot_label
                color=alt.Color(field="is_bot_label", type="nominal", title="Loại"),
                # Tooltip là thông tin hiện ra khi rê chuột
                tooltip=['is_bot_label', 'total_edits']
            ).properties(
                 title='Phân bố Bot vs Người', height=300
            )
            st.altair_chart(chart_bot_human, use_container_width=True)

        except Exception as e:
            st.error(f"Lỗi khi vẽ biểu đồ Bot vs Người thật: {e}")
            # In ra traceback đầy đủ nếu bạn chạy local để debug
            # import traceback
            # st.error(traceback.format_exc())

    else:
        # Giữ lại cảnh báo nếu df_bot_human rỗng ngay từ đầu
        st.warning("Không có dữ liệu Bot vs Người thật để vẽ biểu đồ.")

    st.subheader("👥 Top 10 Người dùng/Bot tích cực")
    df_users = get_data(API_TOP_USERS) # <-- Gọi hàm
    if not df_users.empty:
        st.dataframe(df_users)
    else:
        st.warning("Không có dữ liệu.")
