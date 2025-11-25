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

# 🎨 主題配色庫 (莫蘭迪色系)
THEMES = {
    "⛩️ 京都緋紅 (預設)": {
        "bg": "#FDFCF5", "card": "#FFFFFF", "text": "#2B2B2B", "primary": "#8E2F2F", "secondary": "#D6A6A6", "sub": "#666666"
    },
    "🌫️ 莫蘭迪·霧藍": {
        "bg": "#F0F4F8", "card": "#FFFFFF", "text": "#243B53", "primary": "#486581", "secondary": "#BCCCDC", "sub": "#627D98"
    },
    "🌿 莫蘭迪·鼠尾草": {
        "bg": "#F1F5F1", "card": "#FFFFFF", "text": "#2C3E2C", "primary": "#5F7161", "secondary": "#AFC0B0", "sub": "#506050"
    },
    "🍂 莫蘭迪·焦糖奶茶": {
        "bg": "#FAF6F1", "card": "#FFFFFF", "text": "#4A3B32", "primary": "#9C7C64", "secondary": "#E0D0C5", "sub": "#7D6556"
    },
    "💜 莫蘭迪·紫丁香": {
        "bg": "#Fdfbfd", "card": "#FFFFFF", "text": "#4a3b52", "primary": "#887094", "secondary": "#d6c9dd", "sub": "#6e5d7a"
    },
    "🌾 莫蘭迪·燕麥奶": {
        "bg": "#f9f7f2", "card": "#FFFFFF", "text": "#423e3b", "primary": "#8f8681", "secondary": "#e0dcd8", "sub": "#756f6b"
    },
    "🌲 莫蘭迪·冷杉綠": {
        "bg": "#f0f4f2", "card": "#FFFFFF", "text": "#1a2e26", "primary": "#43665a", "secondary": "#b0c4be", "sub": "#4f635b"
    }
}

# -------------------------------------
# 2. 核心功能函數 & 模擬天氣服務
# -------------------------------------

class WeatherService:
    WEATHER_ICONS = {
        "Sunny": "☀️", "Cloudy": "☁️", "Partly Cloudy": "⛅", 
        "Rainy": "🌧️", "Snowy": "❄️", "Windy": "🍃"
    }
    
    @staticmethod
    def get_forecast(location, date_obj):
        seed_str = f"{location}{date_obj.strftime('%Y%m%d')}"
        random.seed(seed_str)
        month = date_obj.month
        
        base_temp = 20
        weights = [60, 30, 10]
        conditions = ["Sunny", "Cloudy", "Rainy"]

        if month in [12, 1, 2]:
            base_temp = 6
            weights = [40, 40, 10, 10]
            conditions = ["Sunny", "Cloudy", "Snowy", "Rainy"]
        elif month in [6, 7, 8]:
            base_temp = 30
            weights = [50, 20, 30]
        
        high = base_temp + random.randint(0, 5)
        low = base_temp - random.randint(3, 8)
        condition = random.choices(conditions, weights=weights)[0]
        
        return {
            "high": high, "low": low, "condition": condition,
            "icon": WeatherService.WEATHER_ICONS.get(condition, "🌤️"),
            "desc": WeatherService.get_desc(condition, high)
        }

    @staticmethod
    def get_desc(cond, temp):
        if cond == "Rainy": return "有雨，記得帶傘"
        if cond == "Snowy": return "降雪，注意保暖"
        if temp > 30: return "天氣炎熱，多喝水"
        if temp < 10: return "寒冷，建議洋蔥穿搭"
        return "氣候宜人"

def get_packing_recommendations(trip_data, start_date):
    recommendations = set()
    has_rain = False
    min_temp = 100
    max_temp = -100
    
    for day, items in trip_data.items():
        curr_date = start_date + timedelta(days=day-1)
        loc = items[0]['loc'] if items and items[0]['loc'] else "京都"
        w = WeatherService.get_forecast(loc, curr_date)
        if w['condition'] in ["Rainy", "Snowy"]: has_rain = True
        min_temp = min(min_temp, w['low'])
        max_temp = max(max_temp, w['high'])

    if has_rain: recommendations.update(["☔ 折疊傘/雨衣", "👞 防水噴霧"])
    if min_temp < 12: recommendations.update(["🧣 圍巾", "🧥 保暖外套", "🧤 手套"])
    elif min_temp < 20: recommendations.update(["🧥 薄外套"])
    if max_temp > 28: recommendations.update(["🕶️ 太陽眼鏡", "🧢 帽子", "🧴 防曬"])
    
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

def get_category_icon(cat):
    icons = {"trans": "🚃", "food": "🍱", "stay": "🏨", "spot": "⛩️", "shop": "🛍️", "other": "📍"}
    return icons.get(cat, "📍")

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

current_theme = THEMES[st.session_state.selected_theme_name]

if "trip_data" not in st.session_state:
    st.session_state.trip_data = {
        1: [
            {"id": 101, "time": "10:00", "title": "抵達關西機場", "loc": "關西機場", "cost": 0, "cat": "trans", "note": "入境審查、領取周遊券", "expenses": [], "trans_mode": "🚆 電車", "trans_min": 75},
            {"id": 102, "time": "13:00", "title": "京都車站 Check-in", "loc": "KOKO HOTEL 京都", "cost": 0, "cat": "stay", "note": "寄放行李", "expenses": [], "trans_mode": "🚌 巴士", "trans_min": 20},
            {"id": 103, "time": "15:00", "title": "錦市場", "loc": "錦市場", "cost": 2000, "cat": "food", "note": "吃午餐、玉子燒、豆乳甜甜圈", "expenses": [], "trans_mode": "🚶 步行", "trans_min": 15},
            {"id": 104, "time": "18:00", "title": "鴨川散步", "loc": "鴨川", "cost": 0, "cat": "spot", "note": "欣賞夜景", "expenses": [], "trans_mode": "📍 移動", "trans_min": 30}
        ],
        2: [
            {"id": 201, "time": "09:00", "title": "清水寺", "loc": "清水寺", "cost": 400, "cat": "spot", "note": "著名的清水舞台，早點去避開人潮", "expenses": [], "trans_mode": "🚶 步行", "trans_min": 20},
            {"id": 202, "time": "11:00", "title": "二三年坂", "loc": "三年坂", "cost": 1000, "cat": "spot", "note": "古色古香的街道，買伴手禮", "expenses": [], "trans_mode": "🚶 步行", "trans_min": 15},
            {"id": 203, "time": "13:00", "title": "八坂神社", "loc": "八坂神社", "cost": 0, "cat": "spot", "note": "祈求良緣", "expenses": [], "trans_mode": "🚌 巴士", "trans_min": 30},
            {"id": 204, "time": "16:00", "title": "金閣寺", "loc": "金閣寺", "cost": 400, "cat": "spot", "note": "夕陽下的金閣寺最美", "expenses": [], "trans_mode": "📍 移動", "trans_min": 30}
        ],
        3: [
            {"id": 301, "time": "09:00", "title": "伏見稻荷大社", "loc": "伏見稻荷大社", "cost": 0, "cat": "spot", "note": "千本鳥居拍照", "expenses": [], "trans_mode": "🚆 電車", "trans_min": 45},
            {"id": 302, "time": "13:00", "title": "奈良公園", "loc": "奈良公園", "cost": 200, "cat": "spot", "note": "買鹿餅餵鹿 (小心被咬)", "expenses": [], "trans_mode": "🚶 步行", "trans_min": 15},
            {"id": 303, "time": "15:00", "title": "東大寺", "loc": "東大寺", "cost": 600, "cat": "spot", "note": "看巨大佛像", "expenses": [], "trans_mode": "🚆 電車", "trans_min": 60},
            {"id": 304, "time": "19:00", "title": "移動至大阪", "loc": "大阪", "cost": 0, "cat": "trans", "note": "入住大阪飯店", "expenses": [], "trans_mode": "📍 移動", "trans_min": 30}
        ],
        4: [
            {"id": 401, "time": "09:30", "title": "環球影城 (USJ)", "loc": "環球影城", "cost": 9000, "cat": "spot", "note": "馬利歐園區需抽整理券", "expenses": [], "trans_mode": "🚆 電車", "trans_min": 40},
            {"id": 402, "time": "19:00", "title": "道頓堀", "loc": "道頓堀", "cost": 3000, "cat": "food", "note": "跑跑人看板、吃章魚燒、拉麵", "expenses": [], "trans_mode": "📍 移動", "trans_min": 30}
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
# 4. CSS 樣式
# -------------------------------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;700;900&family=Inter:wght@400;600&display=swap');
    
    .stApp {{ 
        background-color: {current_theme['bg']} !important;
        color: {current_theme['text']} !important; 
        font-family: 'Inter', 'Noto Serif JP', sans-serif !important;
    }}

    [data-testid="stSidebarCollapsedControl"], section[data-testid="stSidebar"], 
    div[data-testid="stToolbar"], div[data-testid="stDecoration"], footer {{ display: none !important; }}
    header[data-testid="stHeader"] {{ height: 0 !important; background: transparent !important; }}

    /* Apple Style Cards */
    .apple-card {{
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border-radius: 18px; padding: 20px; margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
    }}
    .apple-time {{ font-weight: 700; font-size: 1.1rem; color: {current_theme['text']}; }}
    .apple-title {{ font-size: 1.1rem; font-weight: 700; margin-bottom: 2px; line-height: 1.4; }}
    .apple-loc {{ font-size: 0.9rem; color: {current_theme['sub']}; display:flex; align-items:center; gap:5px; margin-top:5px; }}
    
    /* Weather Widget */
    .apple-weather-widget {{
        background: linear-gradient(135deg, {current_theme['primary']} 0%, {current_theme['text']} 150%);
        color: white; padding: 15px 20px; border-radius: 20px;
        margin-bottom: 25px; box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        display: flex; align-items: center; justify-content: space-between;
    }}

    /* Day Segmented Control */
    div[data-testid="stRadio"] > div {{
        background-color: {current_theme['secondary']} !important;
        padding: 4px !important; border-radius: 12px !important; gap: 0px !important; border: none !important;
    }}
    div[data-testid="stRadio"] label {{
        background-color: transparent !important; border: none !important;
        flex: 1 !important; text-align: center !important; justify-content: center !important;
        border-radius: 9px !important; height: auto !important; min-width: 50px !important;
    }}
    div[data-testid="stRadio"] label[data-checked="true"] {{
        background-color: {current_theme['card']} !important;
        color: {current_theme['text']} !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important; font-weight: bold !important;
    }}

    /* Info Cards (Tab 2,3,4) */
    .info-card {{
        background-color: {current_theme['card']}; border-radius: 12px; padding: 20px; margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #F0F0F0;
    }}
    .info-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; color: {current_theme['sub']}; font-size: 0.85rem; font-weight: bold; }}
    .info-time {{ font-size: 1.8rem; font-weight: 900; color: {current_theme['text']}; margin-bottom: 5px; font-family: 'Times New Roman', serif; }}
    .info-loc {{ color: {current_theme['sub']}; font-size: 0.9rem; display: flex; align-items: center; gap: 5px; }}
    .info-tag {{ background: {current_theme['bg']}; color: {current_theme['sub']}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }}

    /* Map Route Animation */
    .map-tl-container {{ position: relative; max-width: 100%; margin: 20px auto; padding-left: 30px; }}
    .map-tl-container::before {{
        content: ''; position: absolute; top: 0; bottom: 0; left: 14px; width: 2px;
        background-image: linear-gradient({current_theme['primary']} 40%, rgba(255,255,255,0) 0%);
        background-position: right; background-size: 2px 12px; background-repeat: repeat-y;
    }}
    .map-tl-item {{ position: relative; margin-bottom: 25px; }}
    .map-tl-icon {{
        position: absolute; left: -31px; top: 0px; width: 32px; height: 32px;
        background: {current_theme['card']}; border: 2px solid {current_theme['primary']}; border-radius: 50%;
        text-align: center; line-height: 28px; font-size: 16px; z-index: 2;
    }}
    .map-tl-content {{
        background: {current_theme['card']}; border: 1px solid #E0E0E0; border-left: 4px solid {current_theme['primary']};
        padding: 12px 15px; border-radius: 4px; box-shadow: 0 3px 6px rgba(0,0,0,0.05);
    }}

    /* UI Tweaks */
    button[data-baseweb="tab"] {{ border-radius: 20px !important; margin-right:5px !important; }}
    div[data-baseweb="input"], div[data-baseweb="base-input"] {{ border: none !important; border-bottom: 1px solid {current_theme['secondary']} !important; background: transparent !important; }}
    input {{ color: {current_theme['text']} !important; }}
    </style>
""", unsafe_allow_html=True)

# -------------------------------------
# 5. 主畫面
# -------------------------------------
st.markdown(f'<div style="font-size:2.2rem; font-weight:900; text-align:center; margin-bottom:5px; color:{current_theme["text"]};">{st.session_state.trip_title}</div>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align:center; color:{current_theme["sub"]}; font-size:0.9rem; margin-bottom:20px;">{st.session_state.start_date.strftime("%Y/%m/%d")} 出發</div>', unsafe_allow_html=True)

with st.expander("⚙️ 設定"):
    st.session_state.trip_title = st.text_input("標題", value=st.session_state.trip_title)
    theme_name = st.selectbox("主題", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.selected_theme_name))
    if theme_name != st.session_state.selected_theme_name:
        st.session_state.selected_theme_name = theme_name
        st.rerun()
    c1, c2 = st.columns(2)
    st.session_state.start_date = c1.date_input("日期", value=st.session_state.start_date)
    st.session_state.trip_days_count = c2.number_input("天數", 1, 30, st.session_state.trip_days_count)
    st.session_state.target_country = st.selectbox("地區", ["日本", "韓國", "泰國", "台灣"])
    uf = st.file_uploader("匯入 Excel", type=["xlsx"])
    if uf and st.button("匯入"): process_excel_upload(uf)

# Init Days
for d in range(1, st.session_state.trip_days_count + 1):
    if d not in st.session_state.trip_data: st.session_state.trip_data[d] = []

tab1, tab2, tab3, tab4 = st.tabs(["📅 行程", "🗺️ 路線", "🎒 清單", "ℹ️ 資訊"])

# ==========================================
# 1. 行程規劃 (修復後)
# ==========================================
with tab1:
    selected_day_num = st.radio("DaySelect", list(range(1, st.session_state.trip_days_count + 1)), 
                                index=0, horizontal=True, label_visibility="collapsed", 
                                format_func=lambda x: f"Day {x}")
    
    current_date = st.session_state.start_date + timedelta(days=selected_day_num - 1)
    current_items = st.session_state.trip_data[selected_day_num]
    current_items.sort(key=lambda x: x['time'])
    
    # 計算當日預算
    day_total_cost = sum([item.get('cost', 0) for item in current_items])
    
    # Weather Widget
    first_loc = current_items[0]['loc'] if current_items and current_items[0]['loc'] else (st.session_state.target_country if st.session_state.target_country != "日本" else "京都")
    weather = WeatherService.get_forecast(first_loc, current_date)
    
    st.markdown(f"""
    <div class="apple-weather-widget">
        <div style="display:flex; align-items:center; gap:15px;">
            <div style="font-size:2.5rem;">{weather['icon']}</div>
            <div>
                <div style="font-size:2rem; font-weight:700; line-height:1;">{weather['high']}°</div>
                <div style="font-size:0.9rem; opacity:0.9;">L:{weather['low']}°</div>
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-weight:700;">{current_date.strftime('%m/%d %a')}</div>
            <div style="font-size:0.9rem; opacity:0.9;">📍 {first_loc}</div>
            <div style="font-size:0.8rem; opacity:0.8; margin-top:2px;">{weather['desc']}</div>
        </div>
    </div>
    <div style="text-align:right; font-size:0.8rem; color:{current_theme['sub']}; margin-bottom:10px;">
        本日預估預算: ¥{day_total_cost:,}
    </div>
    """, unsafe_allow_html=True)

    is_edit_mode = st.toggle("編輯模式", value=False)
    if is_edit_mode and st.button("➕ 新增行程", use_container_width=True):
        st.session_state.trip_data[selected_day_num].append({"id": int(datetime.now().timestamp()), "time": "09:00", "title": "新行程", "loc": "", "cost": 0, "cat": "other", "note": "", "expenses": [], "trans_mode": "📍 移動", "trans_min": 30})
        st.rerun()

    # --- 行程列表 (修復縮排與渲染問題) ---
    if not current_items:
        st.info("🍵 點擊「編輯模式」開始安排今日行程")

    for index, item in enumerate(current_items):
        map_link = get_single_map_link(item['loc'])
        map_btn = f'<a href="{map_link}" target="_blank" style="text-decoration:none; margin-left:8px; font-size:0.8rem; background:{current_theme["secondary"]}; color:white; padding:2px 8px; border-radius:10px; opacity:0.8;">🗺️</a>' if item['loc'] else ""
        
        cost_display = ""
        total_exp = sum(x['price'] for x in item.get('expenses', []))
        final_cost = total_exp if total_exp > 0 else item.get('cost', 0)
        if final_cost > 0:
            cost_display = f'<div style="background:{current_theme["primary"]}; color:white; padding:3px 8px; border-radius:12px; font-size:0.75rem; font-weight:bold; white-space:nowrap;">¥{final_cost:,}</div>'

        # 處理 Note 內的換行
        clean_note = item["note"].replace('\n', '<br>')
        note_div = f'<div style="font-size:0.85rem; color:{current_theme["sub"]}; background:{current_theme["bg"]}; padding:8px; border-radius:8px; margin-top:8px; line-height:1.4;">📝 {clean_note}</div>' if item['note'] and not is_edit_mode else ""
        
        # HTML 字串不可縮排，否則會被視為 Code Block
        card_content = f"""
<div style="display:flex; gap:15px; margin-bottom:0px;">
    <div style="display:flex; flex-direction:column; align-items:center; width:50px;">
        <div style="font-weight:700; color:{current_theme['text']}; font-size:1.1rem;">{item['time']}</div>
        <div style="flex-grow:1; width:2px; background:{current_theme['secondary']}; margin:5px 0; opacity:0.3; border-radius:2px;"></div>
    </div>
    <div style="flex-grow:1;">
        <div class="apple-card" style="margin-bottom:15px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div class="apple-title" style="margin-top:0;">{item['title']}</div>
                {cost_display}
            </div>
            <div class="apple-loc">
                📍 {item['loc'] or '未設定'} {map_btn}
            </div>
            {note_div}
        </div>
    </div>
</div>"""
        st.markdown(card_content, unsafe_allow_html=True)

        if is_edit_mode:
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                item['title'] = c1.text_input("名稱", item['title'], key=f"t_{item['id']}")
                item['time'] = c2.time_input("時間", datetime.strptime(item['time'], "%H:%M").time(), key=f"tm_{item['id']}").strftime("%H:%M")
                item['loc'] = st.text_input("地點", item['loc'], key=f"l_{item['id']}")
                item['cost'] = st.number_input("預算 (¥)", value=item['cost'], step=100, key=f"c_{item['id']}")
                item['note'] = st.text_area("備註", item['note'], key=f"n_{item['id']}")
                if st.button("🗑️ 刪除", key=f"del_{item['id']}"):
                    st.session_state.trip_data[selected_day_num].pop(index)
                    st.rerun()

    if current_items:
        route_url = generate_google_map_route(current_items)
        st.markdown(f"<div style='text-align:center; margin-top:20px; margin-bottom:40px;'><a href='{route_url}' target='_blank' style='background:{current_theme['primary']}; color:white; padding:12px 30px; border-radius:30px; text-decoration:none; font-weight:bold; box-shadow:0 4px 10px rgba(0,0,0,0.2);'>🚗 開啟 Google Maps 導航</a></div>", unsafe_allow_html=True)


# ==========================================
# 2. 路線全覽
# ==========================================
with tab2:
    st.markdown(f'<div style="text-align:center; color:{current_theme["sub"]}; font-weight:bold; margin-bottom:15px;">VISUAL ROUTE MAP</div>', unsafe_allow_html=True)
    map_day = st.selectbox("選擇天數", list(range(1, st.session_state.trip_days_count + 1)), format_func=lambda x: f"Day {x}")
    map_items = sorted(st.session_state.trip_data[map_day], key=lambda x: x['time'])
    
    if map_items:
        t_html = ['<div class="map-tl-container">']
        for item in map_items:
            icon = get_category_icon(item.get('cat', 'other'))
            t_html.append(f"""
            <div class='map-tl-item'>
                <div class='map-tl-icon'>{icon}</div>
                <div class='map-tl-content'>
                    <div style='color:{current_theme['primary']}; font-weight:bold;'>{item['time']}</div>
                    <div style='font-weight:900; font-size:1.1rem; color:{current_theme['text']};'>{item['title']}</div>
                    <div style='font-size:0.85rem; color:{current_theme['sub']};'>📍 {item['loc']}</div>
                </div>
            </div>""")
        t_html.append('</div>')
        st.markdown("".join(t_html), unsafe_allow_html=True)
    else:
        st.info("🌸 本日尚無行程")

# ==========================================
# 3. 準備清單
# ==========================================
with tab3:
    recs, weather_summary = get_packing_recommendations(st.session_state.trip_data, st.session_state.start_date)
    st.info(f"**🌤️ 智能穿搭推薦**\n\n預測氣溫：{weather_summary['min']}°C ~ {weather_summary['max']}°C\n\n建議攜帶：" + "、".join(recs))

    c_list_head, c_list_edit = st.columns([3, 1])
    c_list_head.subheader("🎒 準備清單")
    edit_list_mode = c_list_edit.toggle("編輯")

    for category, items in st.session_state.checklist.items():
        st.markdown(f"**{category}**")
        cols = st.columns(2)
        keys_del = []
        for i, (item, checked) in enumerate(items.items()):
            col = cols[i % 2]
            if edit_list_mode:
                c1, c2 = col.columns([4,1])
                c1.text(item)
                if c2.button("x", key=f"d_{category}_{item}"): keys_del.append(item)
            else:
                st.session_state.checklist[category][item] = col.checkbox(item, value=checked, key=f"c_{category}_{item}")
        if keys_del:
            for k in keys_del: del st.session_state.checklist[category][k]
            st.rerun()
        if edit_list_mode:
            new_i = st.text_input(f"加到 {category}", key=f"n_{category}")
            if new_i and st.button("➕", key=f"btn_{category}"):
                st.session_state.checklist[category][new_i] = False
                st.rerun()

    st.markdown("---")
    country = st.session_state.target_country
    st.markdown(f"### 🌍 當地旅遊資訊 ({country})")
    
    trip_month = st.session_state.start_date.month
    season_info = ""
    weather_icon = "🌤️"
    
    if 3 <= trip_month <= 5:
        season_info = "春季：氣候宜人但早晚偏涼，適合洋蔥式穿搭。"
        weather_icon = "🌸"
    elif 6 <= trip_month <= 8:
        season_info = "夏季：炎熱潮濕，注意防曬與補充水分。"
        weather_icon = "☀️"
    elif 9 <= trip_month <= 11:
        season_info = "秋季：涼爽舒適，是旅遊的最佳季節。"
        weather_icon = "🍁"
    else:
        season_info = "冬季：寒冷乾燥，需準備保暖大衣。"
        weather_icon = "❄️"
    
    voltage_info = "100V (雙平腳)"
    sos_info = "警察 110 / 救護 119"
    tip_info = "無小費文化，餐廳含稅。"
    
    if country == "韓國":
        voltage_info = "220V (兩孔圓形)"
        sos_info = "警察 112 / 救護 119"
    elif country == "泰國":
        voltage_info = "220V (雙平腳/兩孔圓)"
        sos_info = "觀光警察 1155"
        tip_info = "有小費習慣，按摩約 50-100 泰銖。"
    elif country == "台灣":
        voltage_info = "110V (雙平腳)"
    
    c_info1, c_info2 = st.columns(2)
    with c_info1:
        st.info(f"**{weather_icon} {trip_month}月氣候建議**\n\n{season_info}")
        st.success(f"**🔌 電壓**\n\n{voltage_info}")
    with c_info2:
        st.warning(f"**🚑 緊急電話**\n\n{sos_info}")
        st.error(f"**💴 小費與消費**\n\n{tip_info}")

# ==========================================
# 4. 重要資訊
# ==========================================
with tab4:
    st.subheader("✈️ 航班")
    flights = st.session_state.flight_info
    out_f, in_f = flights["outbound"], flights["inbound"]
    
    st.markdown(f"""<div class="info-card"><div class="info-header"><span>📅 {out_f['date']}</span> <span>✈️ {out_f['code']}</span></div><div class="info-time">{out_f['dep']} -> {out_f['arr']}</div><div class="info-loc"><span>📍 {out_f['dep_loc']}</span> <span style="margin:0 5px;">✈</span> <span>{out_f['arr_loc']}</span></div><div style="text-align:right; margin-top:5px;"><span class="info-tag">去程</span></div></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="info-card"><div class="info-header"><span>📅 {in_f['date']}</span> <span>✈️ {in_f['code']}</span></div><div class="info-time">{in_f['dep']} -> {in_f['arr']}</div><div class="info-loc"><span>📍 {in_f['dep_loc']}</span> <span style="margin:0 5px;">✈</span> <span>{in_f['arr_loc']}</span></div><div style="text-align:right; margin-top:5px;"><span class="info-tag">回程</span></div></div>""", unsafe_allow_html=True)

    st.divider()
    st.subheader("🏨 住宿")
    for hotel in st.session_state.hotel_info:
        hotel_html = f"""<div class="info-card" style="border-left: 5px solid {current_theme['primary']};"><div class="info-header"><span class="info-tag" style="background:{current_theme['primary']}; color:white;">{hotel['range']}</span><span>{hotel['date']}</span></div><div style="font-size:1.3rem; font-weight:900; color:{current_theme['text']}; margin: 10px 0;">{hotel['name']}</div><div class="info-loc" style="margin-bottom:10px;">📍 {hotel['addr']}</div><a href="{hotel['link']}" target="_blank" style="text-decoration:none; color:{current_theme['primary']}; font-size:0.9rem; font-weight:bold; border:1px solid {current_theme['primary']}; padding:4px 12px; border-radius:20px;">🗺️ 地圖</a></div>"""
        st.markdown(hotel_html, unsafe_allow_html=True)
