import streamlit as st
from datetime import datetime, timedelta
import urllib.parse
import time
import math
import pandas as pd
import random

# -------------------------------------
# 1. 系統設定 & 主題定義
# -------------------------------------
st.set_page_config(page_title="2026 旅程規劃 Pro", page_icon="✈️", layout="centered", initial_sidebar_state="collapsed")

# 🎨 主題配色庫 (保留顏色，但調整為更適合 iOS 風格的應用)
THEMES = {
    "⛩️ 京都緋紅 (預設)": {
        "bg": "#F5F5F7", "card": "rgba(255, 255, 255, 0.7)", "text": "#1D1D1F", "primary": "#8E2F2F", "secondary": "#E5E5EA", "sub": "#86868B"
    },
    "🌫️ 莫蘭迪·霧藍": {
        "bg": "#F2F4F6", "card": "rgba(255, 255, 255, 0.7)", "text": "#1D1D1F", "primary": "#486581", "secondary": "#E5E5EA", "sub": "#627D98"
    },
    "🌿 莫蘭迪·鼠尾草": {
        "bg": "#F2F4F2", "card": "rgba(255, 255, 255, 0.7)", "text": "#1D1D1F", "primary": "#5F7161", "secondary": "#E5E5EA", "sub": "#506050"
    },
    "🌑 深色模式·極簡": {
        "bg": "#000000", "card": "rgba(28, 28, 30, 0.8)", "text": "#F5F5F7", "primary": "#0A84FF", "secondary": "#3A3A3C", "sub": "#8E8E93"
    }
}

# -------------------------------------
# 2. 核心功能函數 & 模擬天氣服務
# -------------------------------------

class WeatherService:
    """
    模擬天氣服務：因為 Streamlit Share 無法直接獲取即時天氣 API Key，
    這裡使用基於歷史數據與雜湊算法的模擬器，確保同一天同一地點的天氣是一致的。
    """
    WEATHER_ICONS = {
        "Sunny": "☀️", "Cloudy": "☁️", "Partly Cloudy": "⛅", 
        "Rainy": "🌧️", "Snowy": "❄️", "Windy": "🍃"
    }
    
    @staticmethod
    def get_forecast(location, date_obj):
        # 使用地點+日期作為種子，確保結果固定
        seed_str = f"{location}{date_obj.strftime('%Y%m%d')}"
        random.seed(seed_str)
        
        month = date_obj.month
        
        # 簡易氣候模型 (以日本/台灣/韓國為主)
        base_temp = 20
        condition_weights = ["Sunny", "Cloudy", "Rainy"]
        weights = [60, 30, 10]
        
        if month in [12, 1, 2]: # 冬季
            base_temp = 5
            condition_weights = ["Sunny", "Cloudy", "Snowy", "Rainy"]
            weights = [40, 40, 10, 10]
            if "台北" in location or "台灣" in location:
                base_temp = 16
                weights = [20, 50, 0, 30]
        elif month in [6, 7, 8]: # 夏季
            base_temp = 30
            weights = [50, 20, 30]
        elif month in [3, 4, 5, 9, 10, 11]: # 春秋
            base_temp = 18
            weights = [60, 30, 10]

        # 隨機波動
        high = base_temp + random.randint(0, 5)
        low = base_temp - random.randint(3, 8)
        condition = random.choices(condition_weights, weights=weights)[0]
        
        # 特殊地點修正
        if "室內" in location or "百貨" in location or "地下" in location:
            condition = "Indoor" # 雖不顯示天氣，但邏輯保留
            
        return {
            "high": high,
            "low": low,
            "condition": condition,
            "icon": WeatherService.WEATHER_ICONS.get(condition, "🌤️"),
            "desc": WeatherService.get_desc(condition, high)
        }

    @staticmethod
    def get_desc(cond, temp):
        if cond == "Rainy": return "有雨，記得帶傘"
        if cond == "Snowy": return "降雪，注意保暖"
        if temp > 30: return "天氣炎熱，多喝水"
        if temp < 10: return "寒冷，建議洋蔥式穿搭"
        return "氣候宜人"

def get_packing_recommendations(trip_data, start_date):
    """根據天氣生成推薦清單"""
    recommendations = set()
    has_rain = False
    min_temp = 100
    max_temp = -100
    
    # 掃描所有行程的天氣
    for day, items in trip_data.items():
        curr_date = start_date + timedelta(days=day-1)
        # 取當天第一個地點作為天氣代表
        loc = items[0]['loc'] if items else "京都" 
        weather = WeatherService.get_forecast(loc, curr_date)
        
        if weather['condition'] in ["Rainy", "Snowy"]:
            has_rain = True
        min_temp = min(min_temp, weather['low'])
        max_temp = max(max_temp, weather['high'])

    # 邏輯判斷
    if has_rain:
        recommendations.add("☔ 折疊傘 / 雨衣")
        recommendations.add("👞 防水噴霧 / 備用鞋")
    
    if min_temp < 10:
        recommendations.add("🧣 圍巾 / 毛帽")
        recommendations.add("🧥 發熱衣")
        recommendations.add("🧤 手套")
        recommendations.add("🧴 護手霜 / 護唇膏 (乾燥)")
    elif min_temp < 18:
        recommendations.add("🧥 薄外套 / 針織衫")
    
    if max_temp > 28:
        recommendations.add("🕶️ 太陽眼鏡")
        recommendations.add("🧢 帽子")
        recommendations.add("🧴 防曬乳")
        recommendations.add("🧊 隨身風扇 / 涼感濕巾")

    return list(recommendations), {"min": min_temp, "max": max_temp, "rain": has_rain}


def add_expense_callback(item_id, day_num):
    name_key = f"new_exp_n_{item_id}"
    price_key = f"new_exp_p_{item_id}"
    name = st.session_state.get(name_key, "")
    price = st.session_state.get(price_key, 0)
    if name and price > 0:
        target_item = next((x for x in st.session_state.trip_data[day_num] if x['id'] == item_id), None)
        if target_item:
            if "expenses" not in target_item: target_item["expenses"] = []
            target_item['expenses'].append({"name": name, "price": price})
            target_item['cost'] = sum(x['price'] for x in target_item['expenses'])
            st.session_state[name_key] = ""
            st.session_state[price_key] = 0

def get_single_map_link(location):
    if not location: return "#"
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(location)}"

def generate_google_map_route(items):
    valid_locs = [item['loc'] for item in items if item.get('loc') and item['loc'].strip()]
    if len(valid_locs) < 1: return "#"
    base_url = "https://www.google.com/maps/dir/"
    encoded_locs = [urllib.parse.quote(loc) for loc in valid_locs]
    return base_url + "/".join(encoded_locs)

def process_excel_upload(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file)
        required_cols = ['Day', 'Time', 'Title']
        if not all(col in df.columns for col in required_cols):
            st.error("Excel 格式錯誤：缺少 Day, Time 或 Title 欄位")
            return
        new_trip_data = {}
        for _, row in df.iterrows():
            day = int(row['Day'])
            if day not in new_trip_data: new_trip_data[day] = []
            time_str = row['Time'].strftime("%H:%M") if isinstance(row['Time'], (datetime, pd.Timestamp)) else str(row['Time'])
            item = {
                "id": int(time.time() * 1000) + _, 
                "time": time_str,
                "title": str(row['Title']),
                "loc": str(row.get('Location', '')),
                "cost": int(row.get('Cost', 0)) if pd.notnull(row.get('Cost')) else 0,
                "cat": "other",
                "note": str(row.get('Note', '')),
                "expenses": [],
                "trans_mode": "📍 移動",
                "trans_min": 30
            }
            new_trip_data[day].append(item)
        st.session_state.trip_data = new_trip_data
        st.session_state.trip_days_count = max(new_trip_data.keys())
        st.toast("✅ 行程匯入成功！")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"匯入失敗: {e}")

# -------------------------------------
# 3. 初始化 & 資料
# -------------------------------------
if "trip_title" not in st.session_state: st.session_state.trip_title = "2026 阪京之旅"
if "exchange_rate" not in st.session_state: st.session_state.exchange_rate = 0.215
if "trip_days_count" not in st.session_state: st.session_state.trip_days_count = 5
if "target_country" not in st.session_state: st.session_state.target_country = "日本"
if "selected_theme_name" not in st.session_state: st.session_state.selected_theme_name = "⛩️ 京都緋紅 (預設)"
if "start_date" not in st.session_state: st.session_state.start_date = datetime(2026, 1, 17)

# 獲取當前主題顏色
current_theme = THEMES[st.session_state.selected_theme_name]

if "trip_data" not in st.session_state:
    # (保留原有的 trip_data 初始化代碼，這裡略過以節省篇幅，內容與原檔相同)
    st.session_state.trip_data = {
        1: [
            {"id": 101, "time": "10:00", "title": "抵達關西機場", "loc": "關西機場", "cost": 0, "cat": "trans", "note": "入境審查、領取周遊券", "expenses": [], "trans_mode": "🚆 電車", "trans_min": 75},
            {"id": 102, "time": "13:00", "title": "京都車站 Check-in", "loc": "KOKO HOTEL 京都", "cost": 0, "cat": "stay", "note": "寄放行李", "expenses": [], "trans_mode": "🚌 巴士", "trans_min": 20},
            {"id": 103, "time": "15:00", "title": "錦市場", "loc": "錦市場", "cost": 2000, "cat": "food", "note": "吃午餐、玉子燒、豆乳甜甜圈", "expenses": [], "trans_mode": "🚶 步行", "trans_min": 15},
            {"id": 104, "time": "18:00", "title": "鴨川散步", "loc": "鴨川", "cost": 0, "cat": "spot", "note": "欣賞夜景", "expenses": [], "trans_mode": "📍 移動", "trans_min": 30}
        ],
        2: [
            {"id": 201, "time": "09:00", "title": "清水寺", "loc": "清水寺", "cost": 400, "cat": "spot", "note": "著名的清水舞台", "expenses": [], "trans_mode": "🚶 步行", "trans_min": 20},
            {"id": 202, "time": "11:00", "title": "二三年坂", "loc": "三年坂", "cost": 1000, "cat": "spot", "note": "買伴手禮", "expenses": [], "trans_mode": "🚶 步行", "trans_min": 15},
            {"id": 203, "time": "13:00", "title": "八坂神社", "loc": "八坂神社", "cost": 0, "cat": "spot", "note": "祈求良緣", "expenses": [], "trans_mode": "🚌 巴士", "trans_min": 30},
            {"id": 204, "time": "16:00", "title": "金閣寺", "loc": "金閣寺", "cost": 400, "cat": "spot", "note": "夕陽下的金閣寺最美", "expenses": [], "trans_mode": "📍 移動", "trans_min": 30}
        ],
        3: [
            {"id": 301, "time": "09:00", "title": "伏見稻荷大社", "loc": "伏見稻荷大社", "cost": 0, "cat": "spot", "note": "千本鳥居拍照", "expenses": [], "trans_mode": "🚆 電車", "trans_min": 45},
            {"id": 302, "time": "13:00", "title": "奈良公園", "loc": "奈良公園", "cost": 200, "cat": "spot", "note": "買鹿餅餵鹿", "expenses": [], "trans_mode": "🚶 步行", "trans_min": 15},
            {"id": 303, "time": "15:00", "title": "東大寺", "loc": "東大寺", "cost": 600, "cat": "spot", "note": "看巨大佛像", "expenses": [], "trans_mode": "🚆 電車", "trans_min": 60},
            {"id": 304, "time": "19:00", "title": "移動至大阪", "loc": "大阪", "cost": 0, "cat": "trans", "note": "入住大阪飯店", "expenses": [], "trans_mode": "📍 移動", "trans_min": 30}
        ],
        4: [
            {"id": 401, "time": "09:30", "title": "環球影城 (USJ)", "loc": "環球影城", "cost": 9000, "cat": "spot", "note": "馬利歐園區需抽整理券", "expenses": [], "trans_mode": "🚆 電車", "trans_min": 40},
            {"id": 402, "time": "19:00", "title": "道頓堀", "loc": "道頓堀", "cost": 3000, "cat": "food", "note": "跑跑人看板", "expenses": [], "trans_mode": "📍 移動", "trans_min": 30}
        ],
        5: [
            {"id": 501, "time": "10:00", "title": "黑門市場", "loc": "黑門市場", "cost": 2000, "cat": "food", "note": "大阪的廚房，吃海鮮", "expenses": [], "trans_mode": "🚆 電車", "trans_min": 50},
            {"id": 502, "time": "13:00", "title": "臨空城 Outlet", "loc": "Rinku Premium Outlets", "cost": 10000, "cat": "shop", "note": "最後採買", "expenses": [], "trans_mode": "🚆 電車", "trans_min": 20},
            {"id": 503, "time": "16:00", "title": "前往機場", "loc": "關西機場", "cost": 0, "cat": "trans", "note": "搭機返台", "expenses": [], "trans_mode": "✈️ 飛機", "trans_min": 0}
        ]
    }

if "flight_info" not in st.session_state:
    st.session_state.flight_info = {
        "outbound": {"date": "1/17", "code": "JX821", "dep": "10:00", "arr": "13:30", "dep_loc": "桃機 T1", "arr_loc": "關西機場"},
        "inbound": {"date": "1/22", "code": "JX822", "dep": "15:00", "arr": "17:10", "dep_loc": "關西機場", "arr_loc": "桃機 T1"}
    }

if "hotel_info" not in st.session_state:
    st.session_state.hotel_info = [
        {"id": 1, "name": "KOKO HOTEL 京都", "range": "D1-D3 (3泊)", "date": "1/17 - 1/19", "addr": "京都府京都市...", "link": "https://goo.gl/maps/example"},
        {"id": 2, "name": "相鐵 FRESA INN 大阪", "range": "D4-D5 (2泊)", "date": "1/20 - 1/21", "addr": "大阪府大阪市...", "link": "https://goo.gl/maps/example"}
    ]

default_checklist = {
    "必要證件": {"護照": False, "機票證明": False, "Visit Japan Web": False, "日幣現金": False, "信用卡": False},
    "電子產品": {"手機 & 充電線": False, "行動電源": False, "SIM卡 / Wifi機": False, "轉接頭": False},
    "衣物穿搭": {"換洗衣物": False, "睡衣": False, "好走的鞋子": False, "外套": False},
    "生活用品": {"牙刷牙膏": False, "常備藥": False, "塑膠袋": False, "折疊傘": False}
}
if "checklist" not in st.session_state or not isinstance(st.session_state.checklist.get("必要證件"), dict):
    st.session_state.checklist = default_checklist

TRANSPORT_OPTIONS = ["🚆 電車", "🚌 巴士", "🚶 步行", "🚕 計程車", "🚗 自駕", "🚢 船", "✈️ 飛機"]

# -------------------------------------
# 4. CSS 樣式 (Apple Design / iOS Style)
# -------------------------------------
st.markdown(f"""
    <style>
    /* 全局字體與背景 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {{
        background-color: {current_theme['bg']} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        color: {current_theme['text']} !important;
    }}

    /* 隱藏不需要的 Streamlit 元素 */
    [data-testid="stSidebarCollapsedControl"], section[data-testid="stSidebar"], 
    div[data-testid="stToolbar"], div[data-testid="stDecoration"], footer {{
        display: none !important;
    }}
    header[data-testid="stHeader"] {{ height: 0 !important; background: transparent !important; }}

    /* --- Apple Style Card (Glassmorphism) --- */
    .apple-card {{
        background: {current_theme['card']};
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease;
    }}
    .apple-card:hover {{
        transform: scale(1.005);
    }}

    /* --- Day Selector (iOS Segmented Control 風格) --- */
    div[data-testid="stRadio"] > div {{
        display: flex !important; flex-direction: row !important; overflow-x: auto !important;
        background-color: {current_theme['secondary']} !important;
        padding: 4px !important; border-radius: 12px !important;
        gap: 0px !important; margin-bottom: 15px !important;
    }}
    div[data-testid="stRadio"] label {{
        background-color: transparent !important;
        border: none !important; margin: 0 !important; padding: 6px 15px !important;
        border-radius: 9px !important; box-shadow: none !important;
        flex: 1 !important; text-align: center !important; justify-content: center !important;
        min-width: 60px !important; height: auto !important;
    }}
    div[data-testid="stRadio"] label[data-checked="true"] {{
        background-color: {current_theme['card']} !important;
        color: {current_theme['text']} !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12) !important;
        font-weight: 600 !important;
    }}
    div[data-testid="stRadio"] label[data-checked="false"] {{
        opacity: 0.6;
    }}
    div[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p {{
        font-size: 0.9rem !important; margin: 0 !important; line-height: 1.2 !important;
    }}

    /* --- iOS Style Timeline --- */
    .ios-timeline-container {{
        padding-left: 20px;
        border-left: 2px solid {current_theme['secondary']};
        margin-left: 15px;
        margin-top: 10px;
    }}
    
    .ios-timeline-item {{
        position: relative;
        margin-bottom: 25px;
    }}
    
    .ios-dot {{
        position: absolute; left: -27px; top: 0px;
        width: 12px; height: 12px;
        background-color: {current_theme['bg']};
        border: 3px solid {current_theme['primary']};
        border-radius: 50%;
        z-index: 2;
    }}

    .ios-time {{
        font-size: 0.85rem; font-weight: 600; color: {current_theme['sub']};
        margin-bottom: 4px; display: flex; align-items: center; gap: 6px;
    }}
    
    .ios-title {{
        font-size: 1.1rem; font-weight: 700; color: {current_theme['text']};
        margin-bottom: 2px;
    }}
    
    .ios-loc {{
        font-size: 0.9rem; color: {current_theme['sub']}; display: flex; align-items: center; gap: 4px;
        margin-bottom: 8px;
    }}
    
    .ios-tag {{
        display: inline-block; padding: 2px 8px; border-radius: 12px;
        font-size: 0.75rem; font-weight: 600; margin-left: auto;
        background: {current_theme['secondary']}; color: {current_theme['text']};
    }}

    /* --- Weather Widget --- */
    .weather-widget {{
        display: flex; align-items: center; justify-content: space-between;
        background: linear-gradient(135deg, {current_theme['primary']} 0%, {current_theme['text']} 150%);
        color: white; padding: 15px 20px; border-radius: 20px;
        margin-bottom: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }}
    .weather-temp {{ font-size: 2.2rem; font-weight: 700; }}
    .weather-icon {{ font-size: 2.5rem; }}
    .weather-info {{ text-align: right; }}
    .weather-loc {{ font-size: 0.9rem; opacity: 0.9; }}
    .weather-desc {{ font-size: 0.8rem; opacity: 0.8; margin-top: 2px; }}

    /* --- Transport Pill --- */
    .transport-pill {{
        background: {current_theme['bg']}; color: {current_theme['sub']};
        padding: 4px 10px; border-radius: 15px; font-size: 0.75rem;
        border: 1px solid {current_theme['secondary']};
        display: inline-flex; align-items: center; margin-bottom: 10px;
    }}

    /* --- Map Button --- */
    .ios-btn-small {{
        text-decoration: none; color: {current_theme['primary']}; 
        background: rgba(255,255,255,0.5); border-radius: 12px;
        padding: 2px 8px; font-size: 0.75rem; font-weight: 600;
        margin-left: 5px;
    }}

    /* --- Inputs & Tabs --- */
    input {{ color: {current_theme['text']} !important; }}
    button[data-baseweb="tab"] {{ border-radius: 20px !important; padding: 5px 15px !important; margin-right: 5px !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ background-color: {current_theme['primary']} !important; color: white !important; }}
    
    </style>
""", unsafe_allow_html=True)

# -------------------------------------
# 5. 主畫面
# -------------------------------------
st.markdown(f'<div style="font-size:2rem; font-weight:800; text-align:center; margin-bottom:5px; color:{current_theme["text"]}; letter-spacing: -0.5px;">{st.session_state.trip_title}</div>', unsafe_allow_html=True)

# --- Settings ---
with st.expander("⚙️ 旅程設定"):
    st.session_state.trip_title = st.text_input("旅程標題", value=st.session_state.trip_title)
    theme_name = st.selectbox("主題", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.selected_theme_name))
    if theme_name != st.session_state.selected_theme_name:
        st.session_state.selected_theme_name = theme_name
        st.rerun()

    c1, c2 = st.columns(2)
    st.session_state.start_date = c1.date_input("出發日期", value=st.session_state.start_date)
    st.session_state.trip_days_count = c2.number_input("天數", 1, 30, st.session_state.trip_days_count)
    st.session_state.target_country = st.selectbox("地區", ["日本", "韓國", "泰國", "台灣"], index=0)
    
    uploaded_file = st.file_uploader("匯入 Excel", type=["xlsx"])
    if uploaded_file and st.button("確認匯入"): process_excel_upload(uploaded_file)

# Init Days
for d in range(1, st.session_state.trip_days_count + 1):
    if d not in st.session_state.trip_data: st.session_state.trip_data[d] = []

tab1, tab2, tab3, tab4 = st.tabs(["📅 行程", "🗺️ 地圖", "🎒 清單", "ℹ️ 資訊"])

# ==========================================
# 1. 行程規劃 (Apple Style)
# ==========================================
with tab1:
    # Segmented Control for Days
    selected_day_num = st.radio("DaySelect", list(range(1, st.session_state.trip_days_count + 1)), 
                                index=0, horizontal=True, label_visibility="collapsed", 
                                format_func=lambda x: f"Day {x}")
    
    current_date = st.session_state.start_date + timedelta(days=selected_day_num - 1)
    current_items = st.session_state.trip_data[selected_day_num]
    current_items.sort(key=lambda x: x['time'])
    
    # --- 動態天氣卡片 ---
    first_loc = current_items[0]['loc'] if current_items and current_items[0]['loc'] else (st.session_state.target_country if st.session_state.target_country != "日本" else "京都")
    weather = WeatherService.get_forecast(first_loc, current_date)
    
    st.markdown(f"""
    <div class="weather-widget">
        <div style="display:flex; align-items:center; gap:15px;">
            <div class="weather-icon">{weather['icon']}</div>
            <div>
                <div class="weather-temp">{weather['high']}° <span style="font-size:1.2rem; opacity:0.7;">/ {weather['low']}°</span></div>
            </div>
        </div>
        <div class="weather-info">
            <div style="font-weight:700;">{current_date.strftime('%m/%d')} {current_date.strftime('%A')[:3]}</div>
            <div class="weather-loc">📍 {first_loc}</div>
            <div class="weather-desc">{weather['desc']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 編輯模式開關
    is_edit_mode = st.toggle("編輯模式", value=False)
    if is_edit_mode and st.button("➕ 新增行程", use_container_width=True):
        st.session_state.trip_data[selected_day_num].append({"id": int(datetime.now().timestamp()), "time": "09:00", "title": "新行程", "loc": "", "cost": 0, "cat": "other", "note": "", "expenses": [], "trans_mode": "📍 移動", "trans_min": 30})
        st.rerun()

    # --- iOS 時間軸 ---
    st.markdown('<div class="ios-timeline-container">', unsafe_allow_html=True)
    
    if not current_items:
        st.info("🍵 點擊「編輯模式」開始安排今日行程")

    for index, item in enumerate(current_items):
        # 處理費用
        current_expense_sum = sum(x['price'] for x in item.get('expenses', []))
        display_cost = current_expense_sum if current_expense_sum > 0 else item.get('cost', 0)
        price_html = f'<span class="ios-tag">¥{display_cost:,}</span>' if display_cost > 0 else ""
        
        # 處理連結
        map_link = get_single_map_link(item['loc'])
        map_btn = f'<a href="{map_link}" target="_blank" class="ios-btn-small">🗺️</a>' if item['loc'] else ""
        
        # 處理備註
        note_html = f'<div style="font-size:0.85rem; color:{current_theme["sub"]}; background:{current_theme["bg"]}; padding:8px; border-radius:8px; margin-top:5px;">📝 {item["note"]}</div>' if item['note'] and not is_edit_mode else ""
        
        # 處理記帳顯示
        expense_html = ""
        if item.get('expenses'):
            exp_rows = "".join([f"<div style='display:flex; justify-content:space-between; font-size:0.8rem; margin-top:2px;'><span>{e['name']}</span><span>¥{e['price']}</span></div>" for e in item['expenses']])
            expense_html = f"<div style='margin-top:8px; padding-top:5px; border-top:1px dashed #CCC;'>{exp_rows}</div>"

        # 顯示卡片
        st.markdown(f"""
        <div class="ios-timeline-item">
            <div class="ios-dot"></div>
            <div class="apple-card" style="padding: 15px;">
                <div class="ios-time">
                    {item['time']} {price_html}
                </div>
                <div class="ios-title">{item['title']}</div>
                <div class="ios-loc">📍 {item['loc'] or '未設定'} {map_btn}</div>
                {note_html}
                {expense_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 編輯介面
        if is_edit_mode:
            with st.container(border=True):
                c1, c2 = st.columns([1, 1])
                item['title'] = c1.text_input("名稱", item['title'], key=f"t_{item['id']}")
                item['time'] = c2.time_input("時間", datetime.strptime(item['time'], "%H:%M").time(), key=f"tm_{item['id']}").strftime("%H:%M")
                item['loc'] = st.text_input("地點", item['loc'], key=f"l_{item['id']}")
                item['note'] = st.text_area("備註", item['note'], height=60, key=f"n_{item['id']}")
                
                # 記帳小工具
                ce1, ce2, ce3 = st.columns([2, 1, 1])
                ce1.text_input("項目", key=f"new_exp_n_{item['id']}", placeholder="新增消費", label_visibility="collapsed")
                ce2.number_input("金額", min_value=0, key=f"new_exp_p_{item['id']}", label_visibility="collapsed")
                ce3.button("➕", key=f"add_{item['id']}", on_click=add_expense_callback, args=(item['id'], selected_day_num))
                
                if st.button("🗑️ 刪除", key=f"del_{item['id']}"):
                    st.session_state.trip_data[selected_day_num].pop(index)
                    st.rerun()

        # 交通連接線
        if index < len(current_items) - 1:
            next_item = current_items[index+1]
            tm = item.get('trans_mode', '📍 移動')
            tmin = item.get('trans_min', 30)
            
            if is_edit_mode:
                c_t1, c_t2 = st.columns([1, 1])
                item['trans_mode'] = c_t1.selectbox("交通", TRANSPORT_OPTIONS, key=f"tr_m_{item['id']}")
                item['trans_min'] = c_t2.number_input("分鐘", value=tmin, step=5, key=f"tr_mn_{item['id']}")
            else:
                st.markdown(f'<div style="padding-left:10px; border-left:2px dashed {current_theme["secondary"]}; margin-left:-2px; padding-bottom:15px;"><span class="transport-pill">{tm} {tmin} min</span></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # End Timeline Container
    
    if current_items:
        route_url = generate_google_map_route(current_items)
        st.markdown(f"<div style='text-align:center; margin-top:20px;'><a href='{route_url}' target='_blank' style='background:{current_theme['primary']}; color:white; padding:12px 30px; border-radius:30px; text-decoration:none; font-weight:600; box-shadow:0 4px 10px rgba(0,0,0,0.2);'>🚗 開啟 Google Maps 導航</a></div>", unsafe_allow_html=True)

# ==========================================
# 2. 地圖全覽
# ==========================================
with tab2:
    st.markdown(f'<div style="text-align:center; font-weight:700; color:{current_theme["sub"]}; margin-bottom:20px;">ROUTE VISUALIZATION</div>', unsafe_allow_html=True)
    map_day = st.selectbox("選擇天數", list(range(1, st.session_state.trip_days_count + 1)), format_func=lambda x: f"Day {x}")
    map_items = sorted(st.session_state.trip_data[map_day], key=lambda x: x['time'])
    
    for item in map_items:
        st.markdown(f"""
        <div class="apple-card" style="display:flex; align-items:center; gap:15px;">
            <div style="font-weight:700; color:{current_theme['primary']}; min-width:50px;">{item['time']}</div>
            <div style="flex-grow:1;">
                <div style="font-weight:600;">{item['title']}</div>
                <div style="font-size:0.85rem; color:{current_theme['sub']};">📍 {item['loc']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 3. 準備清單 (含天氣智能推薦)
# ==========================================
with tab3:
    st.subheader("🎒 準備清單")
    
    # --- 智能天氣推薦區塊 ---
    recs, weather_summary = get_packing_recommendations(st.session_state.trip_data, st.session_state.start_date)
    
    with st.container():
        st.markdown(f"""
        <div class="apple-card" style="background: linear-gradient(to right, {current_theme['bg']}, {current_theme['card']});">
            <h4 style="margin:0 0 10px 0;">🌤️ 智能天氣推薦</h4>
            <div style="font-size:0.9rem; margin-bottom:10px;">
                旅程氣溫範圍：<b>{weather_summary['min']}°C ~ {weather_summary['max']}°C</b> 
                {'｜ 🌧️ 會有雨天' if weather_summary['rain'] else '｜ ☀️ 預計無雨'}
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:8px;">
                {''.join([f'<span style="background:{current_theme["primary"]}; color:white; padding:4px 10px; border-radius:12px; font-size:0.85rem;">{r}</span>' for r in recs])}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- 原有清單功能 ---
    col_l1, col_l2 = st.columns([3, 1])
    edit_list = col_l2.toggle("編輯")
    
    for category, items in st.session_state.checklist.items():
        with st.expander(f"📌 {category}", expanded=True):
            for item, checked in list(items.items()):
                if edit_list:
                    c1, c2 = st.columns([4, 1])
                    c1.text(item)
                    if c2.button("✕", key=f"del_{category}_{item}"):
                        del st.session_state.checklist[category][item]
                        st.rerun()
                else:
                    st.session_state.checklist[category][item] = st.checkbox(item, value=checked, key=f"chk_{category}_{item}")
            
            if edit_list:
                new_i = st.text_input("新增項目", key=f"new_i_{category}")
                if new_i and st.button("加入", key=f"add_i_{category}"):
                    st.session_state.checklist[category][new_i] = False
                    st.rerun()

# ==========================================
# 4. 重要資訊
# ==========================================
with tab4:
    # 航班卡片
    st.subheader("✈️ 航班資訊")
    f_out = st.session_state.flight_info['outbound']
    f_in = st.session_state.flight_info['inbound']
    
    for f_type, f_data, label in [("outbound", f_out, "去程"), ("inbound", f_in, "回程")]:
        st.markdown(f"""
        <div class="apple-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span class="ios-tag" style="background:{current_theme['primary']}; color:white;">{label}</span>
                <span style="font-weight:600;">{f_data['date']}</span>
            </div>
            <div style="font-size:1.5rem; font-weight:800; margin-bottom:5px;">{f_data['dep']} ➝ {f_data['arr']}</div>
            <div style="color:{current_theme['sub']}; font-size:0.9rem;">
                {f_data['code']} ｜ {f_data['dep_loc']} - {f_data['arr_loc']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 住宿卡片
    st.subheader("🏨 住宿安排")
    for h in st.session_state.hotel_info:
        st.markdown(f"""
        <div class="apple-card">
            <div style="font-weight:700; font-size:1.1rem; margin-bottom:5px;">{h['name']}</div>
            <div style="font-size:0.9rem; color:{current_theme['sub']}; margin-bottom:10px;">{h['range']} ({h['date']})</div>
            <div style="font-size:0.85rem;">📍 {h['addr']}</div>
            <div style="margin-top:10px;"><a href="{h['link']}" target="_blank" class="ios-btn-small">🗺️ 查看地圖</a></div>
        </div>
        """, unsafe_allow_html=True)
