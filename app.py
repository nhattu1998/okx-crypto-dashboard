import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import json

class OKXCryptoDashboard:
    def __init__(self):
        self.base_url = "https://www.okx.com"
        self.api_base = "https://www.okx.com/api/v5"
        
    def get_funding_rates(self):
        """Lấy funding rates của các cặp USDT"""
        try:
            url = f"{self.api_base}/public/funding-rate"
            params = {
                'instType': 'SWAP',
                'uly': 'USDT'
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()['data']
            return []
        except Exception as e:
            st.error(f"Lỗi khi lấy funding rate: {e}")
            return []
    
    def get_long_short_ratio(self, inst_id="BTC-USDT"):
        """Lấy tỷ lệ Long/Short"""
        try:
            url = f"{self.api_base}/rubik/stat/contracts/long-short-account-ratio"
            params = {
                'ccy': inst_id.split('-')[0],
                'period': '5m'
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()['data']
                return data
            return []
        except Exception as e:
            # Không hiển thị lỗi để tránh spam
            return []
    
    def get_ticker_data(self):
        """Lấy dữ liệu ticker cho tất cả cặp USDT"""
        try:
            url = f"{self.api_base}/market/tickers"
            params = {'instType': 'SWAP'}
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()['data']
                # Lọc chỉ các cặp USDT
                usdt_pairs = [item for item in data if item['instId'].endswith('-USDT-SWAP')]
                return usdt_pairs
            return []
        except Exception as e:
            st.error(f"Lỗi khi lấy dữ liệu ticker: {e}")
            return []
    
    @st.cache_data(ttl=300)  # Cache 5 phút
    def get_market_data(_self):
        """Lấy dữ liệu thị trường tổng hợp"""
        ticker_data = _self.get_ticker_data()
        funding_data = _self.get_funding_rates()
        
        # Tạo dictionary để tra cứu funding rate
        funding_dict = {item['instId']: float(item['fundingRate']) * 100 for item in funding_data}
        
        processed_data = []
        # Giới hạn 30 coin để tránh timeout
        for ticker in ticker_data[:30]:
            inst_id = ticker['instId']
            coin_name = inst_id.replace('-USDT-SWAP', '')
            
            # Lấy tỷ lệ Long/Short với xử lý lỗi
            long_ratio = 50  # Mặc định
            short_ratio = 50
            
            try:
                ls_data = _self.get_long_short_ratio(f"{coin_name}-USDT")
                if ls_data and len(ls_data) > 0:
                    # Tính toán từ dữ liệu API
                    long_account = float(ls_data[0].get('longAccount', 0.5))
                    short_account = float(ls_data[0].get('shortAccount', 0.5))
                    total = long_account + short_account
                    if total > 0:
                        long_ratio = (long_account / total) * 100
                        short_ratio = (short_account / total) * 100
            except:
                # Giữ giá trị mặc định
                pass
            
            processed_data.append({
                'Coin': coin_name,
                'Giá': float(ticker['last']),
                'Thay đổi 24h (%)': float(ticker['chg']) * 100,
                'Volume 24h': float(ticker['volCcy24h']),
                'Long (%)': round(long_ratio, 2),
                'Short (%)': round(short_ratio, 2),
                'Funding Rate (%)': round(funding_dict.get(inst_id, 0) * 8760, 4),  # Năm hóa
                'Cập nhật': datetime.now().strftime("%H:%M:%S")
            })
            
        return processed_data

def create_dashboard():
    st.set_page_config(
        page_title="📊 OKX Crypto Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    # CSS để responsive
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }
        @media (max-width: 768px) {
            .stDataFrame {
                width: 100%;
                font-size: 12px;
            }
        }
        .metric-card {
            background: linear-gradient(90deg, #1f77b4, #17a2b8);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📊 OKX Signal Center - Dashboard Tiền Điện Tử")
    st.markdown("*Cập nhật mỗi 15 phút - Dữ liệu từ sàn OKX*")
    
    # Sidebar controls
    st.sidebar.header("⚙️ Cài đặt")
    auto_refresh = st.sidebar.checkbox("Tự động làm mới", value=False)
    refresh_interval = st.sidebar.selectbox("Khoảng thời gian (giây)", [15, 30, 60, 300], index=3)
    show_charts = st.sidebar.checkbox("Hiển thị biểu đồ", value=True)
    
    # Tạo instance dashboard
    dashboard = OKXCryptoDashboard()
    
    # Placeholder cho dữ liệu
    data_placeholder = st.empty()
    chart_placeholder = st.empty()
    
    # Hàm cập nhật dữ liệu
    def update_data():
        with st.spinner("🔄 Đang tải dữ liệu từ OKX..."):
            try:
                market_data = dashboard.get_market_data()
            except Exception as e:
                st.error(f"Lỗi khi tải dữ liệu: {e}")
                return
            
        if market_data:
            df = pd.DataFrame(market_data)
            
            with data_placeholder.container():
                # Metrics tổng quan
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Tổng số Coin", len(df))
                with col2:
                    avg_long = df['Long (%)'].mean()
                    st.metric("Long trung bình", f"{avg_long:.1f}%")
                with col3:
                    positive_change = len(df[df['Thay đổi 24h (%)'] > 0])
                    st.metric("Tăng giá (24h)", f"{positive_change}/{len(df)}")
                with col4:
                    avg_funding = df['Funding Rate (%)'].mean()
                    st.metric("Funding TB", f"{avg_funding:.3f}%")
                
                st.subheader("📈 Dữ liệu Chi tiết")
                
                # Định dạng hiển thị
                styled_df = df.copy()
                styled_df['Giá'] = styled_df['Giá'].apply(lambda x: f"${x:,.4f}")
                styled_df['Volume 24h'] = styled_df['Volume 24h'].apply(lambda x: f"${x:,.0f}")
                
                # Tô màu cho các cột
                def color_change(val):
                    try:
                        val_num = float(val)
                        color = 'color: green' if val_num > 0 else 'color: red' if val_num < 0 else 'color: gray'
                        return color
                    except:
                        return ''
                
                def color_long_short(val, threshold=60):
                    try:
                        val_num = float(val)
                        if val_num > threshold:
                            return 'background-color: rgba(255, 0, 0, 0.3)'
                        elif val_num < (100 - threshold):
                            return 'background-color: rgba(0, 255, 0, 0.3)'
                        return ''
                    except:
                        return ''
                
                st.dataframe(
                    styled_df.style.applymap(color_change, subset=['Thay đổi 24h (%)', 'Funding Rate (%)'])
                                   .applymap(lambda x: color_long_short(x, 65), subset=['Long (%)'])
                                   .applymap(lambda x: color_long_short(x, 65), subset=['Short (%)']),
                    use_container_width=True,
                    height=600
                )
            
            # Biểu đồ (tùy chọn)
            if show_charts:
                with chart_placeholder.container():
                    st.subheader("📊 Biểu đồ Phân tích")
                    
                    tab1, tab2, tab3 = st.tabs(["Long/Short Ratio", "Price Change", "Funding Rates"])
                    
                    with tab1:
                        fig1 = go.Figure()
                        fig1.add_trace(go.Bar(
                            name='Long %',
                            x=df['Coin'][:20],
                            y=df['Long (%)'][:20],
                            marker_color='green',
                            opacity=0.7
                        ))
                        fig1.add_trace(go.Bar(
                            name='Short %',
                            x=df['Coin'][:20],
                            y=df['Short (%)'][:20],
                            marker_color='red',
                            opacity=0.7
                        ))
                        fig1.update_layout(
                            title='Tỷ lệ Long/Short Top 20 Coin',
                            xaxis_title='Coin',
                            yaxis_title='Phần trăm (%)',
                            barmode='stack',
                            height=500
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                    
                    with tab2:
                        fig2 = px.bar(
                            df.head(20),
                            x='Coin',
                            y='Thay đổi 24h (%)',
                            title='Biến động giá 24h Top 20 Coin',
                            color='Thay đổi 24h (%)',
                            color_continuous_scale=['red', 'gray', 'green']
                        )
                        fig2.update_layout(height=500)
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    with tab3:
                        fig3 = px.scatter(
                            df,
                            x='Long (%)',
                            y='Funding Rate (%)',
                            size='Volume 24h',
                            hover_data=['Coin', 'Giá'],
                            title='Mối quan hệ Long% vs Funding Rate',
                            color='Thay đổi 24h (%)',
                            color_continuous_scale=['red', 'gray', 'green']
                        )
                        fig3.update_layout(height=500)
                        st.plotly_chart(fig3, use_container_width=True)
        else:
            st.error("❌ Không thể tải dữ liệu từ OKX. Vui lòng thử lại!")
    
    # Cập nhật dữ liệu lần đầu
    update_data()
    
    # Auto refresh logic
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()
    
    # Nút refresh thủ công
    if st.sidebar.button("🔄 Làm mới ngay"):
        st.rerun()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("🚀 **OKX Crypto Dashboard**")
    st.sidebar.markdown("📊 Made with Streamlit")
    st.sidebar.markdown("⚡ Real-time data from OKX")

# Chạy ứng dụng
if __name__ == "__main__":
    create_dashboard()
