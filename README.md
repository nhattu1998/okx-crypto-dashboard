# 📊 OKX Crypto Dashboard

Dashboard thống kê thời gian thực cho các cặp tiền điện tử USDT trên sàn OKX.

## ✨ Tính năng

- 📈 Hiển thị tỷ lệ Long/Short ratio
- 💰 Funding rates và biến động giá 24h
- 📊 Biểu đồ tương tác với Plotly
- 🔄 Tự động cập nhật dữ liệu
- 📱 Responsive design cho mobile

## 🚀 Demo

Xem dashboard tại: [Link sẽ được tạo sau khi deploy]

## 🛠️ Công nghệ sử dụng

- **Streamlit** - Web framework
- **Plotly** - Biểu đồ tương tác  
- **Pandas** - Xử lý dữ liệu
- **OKX API** - Nguồn dữ liệu thời gian thực

## 📊 Dữ liệu hiển thị

- Giá hiện tại và biến động 24h
- Volume giao dịch 24h
- Tỷ lệ Long/Short của traders
- Funding rates (năm hóa)
- Biểu đồ phân tích kỹ thuật

## 🔧 Cài đặt local

```bash
pip install -r requirements.txt
streamlit run app.py
