import streamlit as st
from datetime import datetime
import urllib.parse
import time
import re
import textwrap # 新增這個庫來處理縮排問題

# -------------------------------------
# 1. 系統設定 & CSS 樣式 (強制修正顏色與縮排)
# -------------------------------------
st.set_page_config(page_title="2026 阪京自駕遊", page_icon="🇯🇵", layout="centered", initial_sidebar_state="collapsed")

# 配色主題
THEME = {
    "bg": "#FDFCF5", "card": "#FFFFFF", "text": "#2B2B2B", 
    "primary": "#8E2F2F", "secondary": "#D6A6A6", "sub": "#666666",
    "guide_bg": "#FFF8E1", "guide_border": "#FFE082"
}

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    /* 強制全域字體顏色為深色 (解決手機深色模式下字變白的問題) */
    .stApp, .stMarkdown, p, div, span, label {{ 
        background-color: {THEME['bg']} !important;
        color: {THEME['text']} !important; 
        font-family: 'Noto Sans TC', sans-serif !important;
    }}
    
    /* 特別針對 Radio Button (天數選擇) 的文字修復 */
    .stRadio label, .stRadio div[data-testid="stMarkdownContainer"] p {{
        color: {THEME['text']} !important;
        font-weight: bold;
    }}

    /* 隱藏多餘元件 */
    header, footer, [data-testid="stToolbar"] {{ display: none !important; }}

    /* 天氣 Widget */
    .weather-widget {{
        background: linear-gradient(135deg, {THEME['primary']} 0%, {THEME['secondary']} 100%) !important;
        color: white !important; /* 這裡強制白色，因為背景是深色漸層 */
        border-radius: 16px; padding: 15px 20px;
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }}
    /* 修正天氣內的文字顏色，避免被全域 CSS 覆蓋 */
    .weather-widget div, .weather-widget span {{
        background-color: transparent !important;
        color: white !important;
    }}
    .weather-temp {{ font-size: 2rem; font-weight: 700; line-height: 1; }}

    /* 行程卡片 */
    .app-card {{
        background: {THEME['card']} !important; 
        border-radius: 16px; padding: 16px;
        margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid rgba(0,0,0,0.02); position: relative; overflow: hidden;
    }}
    .category-strip {{
        position: absolute; left: 0; top: 0; bottom: 0; width: 6px;
    }}
    .card-header {{ display: flex; justify-content: space-between; margin-bottom: 6px; }}
    .card-time {{ font-weight: 700; font-size: 1.1rem; }}
    .card-title {{ font-size: 1.2rem; font-weight: 700; margin-bottom: 6px; }}
    
    /* 導航按鈕 */
    .nav-btn {{
        background: #fff !important; color: {THEME['primary']} !important; 
        border: 1px solid {THEME['primary']};
        padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; 
        text-decoration: none; display: inline-block;
    }}

    /* 👨‍🏫 導遊情報區塊 */
    .guide-box {{
        background-color: {THEME['guide_bg']} !important;
        border-left: 4px solid {THEME['guide_border']};
        padding: 10px 12px; margin-top: 12px; border-radius: 4px;
        font-size: 0.9rem; color: #5d4037 !important;
    }}
    .guide-label {{
        font-weight: bold; color: #ff6f00 !important; margin-right: 5px;
        display: block; margin-bottom: 2px; margin-top: 6px;
        background-color: transparent !important;
    }}
    
    /* 輸入框優化 */
    .stTextInput input, .stNumberInput input {{
        background: {THEME['card']} !important; border-radius: 8px;
        color: {THEME['text']} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# -------------------------------------
# 2. 模擬導遊資料庫
# -------------------------------------
GUIDE_DB = {
    "Outlet": {
        "story": "臨空城 Outlet 是西日本最大規模，建築風格模仿美國查爾斯頓港口。",
        "food": "KUA`AINA 夏威夷漢堡 (歐巴馬最愛)、抹茶館 Maccha House",
        "buy": "Nike/Adidas 運動鞋(常有3折)、KitKat 關西限定口味"
    },
    "貴志": {
        "story": "著名的「貓站長」小玉駐守的車站，車站建築本身就是貓咪臉型設計。",
        "food": "車站內的「小玉咖啡廳」必點貓掌泡芙。",
        "buy": "小玉站長徽章、貓咪明信片、和歌山蜜柑果汁"
    },
    "白濱": {
        "story": "日本三大古湯之一，擁有超過1300年歷史，這裡的白良濱沙灘沙質雪白。",
        "food": "「幻之魚」九繪 (Kue) 火鍋、ToreTore 市場的海鮮丼。",
        "buy": "紀州梅乾 (梅翁園)、柚子酒、熊野牛咖哩包"
    },
    "租車": {
        "story": "日本自駕需準備：台灣駕照、日文譯本 (非國際駕照)、護照。",
        "food": "高速公路休息站 (SA/PA) 的拉麵意外好吃！",
        "buy": "ETC 卡 (記得選購 KEP pass 較划算)"
    }
}

def get_ai_guide(title, location):
    search_text = (str(title) + str(location)).lower()
    for key, info in GUIDE_DB.items():
        if key.lower() in search_text:
            return info
    return None

def auto_highlight_text(text):
    if not text: return ""
    # 使用 span 並強制設定樣式，防止被 Markdown code block 影響
    text = re.sub(r'(必吃|推薦|名物)', r'<span style="background:#FF8C42; color:white; padding:2px 6px; border-radius:4px; font-size:0.8rem;">🍱 \1</span>', text)
    text = re.sub(r'(必買|伴手禮|限定)', r'<span style="background:#E63946; color:white; padding:2px 6px; border-radius:4px; font-size:0.8rem;">🛍️ \1</span>', text)
    text = re.sub(r'(預約|代號)', r'<span style="background:#2A9D8F; color:white; padding:2px 6px; border-radius:4px; font-size:0.8rem;">🎫 \1</span>', text)
    return text

def get_nav_link(location):
    if not location: return "#"
    return f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(location)}&travelmode=driving"

# -------------------------------------
# 3. 資料初始化
# -------------------------------------
if "trip_data" not in st.session_state:
    st.session_state.trip_data = {
        1: [
            {"id": 101, "time": "10:00", "title": "關西機場 租車", "loc": "關西國際機場 Aeroplaza", "cost": 15000, "cat": "trans", "note": "預約代號：KIX-CAR-8821。記得攜帶駕照譯本。", "trans_mode": "🚗 自駕", "trans_min": 20},
            {"id": 102, "time": "12:30", "title": "臨空城 Outlet 午餐", "loc": "Rinku Premium Outlets", "cost": 3000, "cat": "food", "note": "必吃 KUA`AINA 漢堡。順便去 Adidas 看鞋子。", "trans_mode": "🚗 自駕", "trans_min": 60},
            {"id": 103, "time": "15:00", "title": "貴志車站看貓站長", "loc": "和歌山 貴志駅", "cost": 0, "cat": "spot", "note": "必買 貓咪站長周邊。", "trans_mode": "🚗 自駕", "trans_min": 90},
            {"id": 104, "time": "18:00", "title": "白濱溫泉 飯店", "loc": "白濱萬豪酒店", "cost": 0, "cat": "stay", "note": "Check-in 完去泡湯。", "trans_mode": "😴 休息", "trans_min": 0}
        ],
        2: [], 3: [], 4: [], 5: []
    }

if "pack_list" not in st.session_state:
    st.session_state.pack_list = {
        "證件": {"護照": False, "駕照譯本": False, "機票證明": False},
        "電子": {"網卡/漫遊": False, "充電器": False, "行動電源": False},
        "生活": {"常備藥": False, "雨具": False, "口罩": False}
    }

# -------------------------------------
# 4. 主介面
# -------------------------------------
st.markdown("<h1 style='text-align: center;'>2026 阪京自駕遊 🇯🇵</h1>", unsafe_allow_html=True)

# 分頁
tab_schedule, tab_map, tab_info = st.tabs(["📅 每日行程", "🗺️ 地圖路線", "ℹ️ 重要資訊"])

# ==========================================
# Tab 1: 每日行程
# ==========================================
with tab_schedule:
    days = sorted(list(st.session_state.trip_data.keys()))
    # 天數選擇
    selected_day = st.radio("選擇天數", days, format_func=lambda x: f"第 {x} 天", horizontal=True)
    
    # 天氣 Widget
    w_info = {1: "🌤️ 12°C | 晴時多雲", 2: "🌧️ 10°C | 短暫雨", 3: "☁️ 11°C | 陰天"}
    weather_text = w_info.get(selected_day, "☀️ 14°C | 晴朗")
    
    # 修正：移除縮排，防止被視為 Code Block
    st.markdown(textwrap.dedent(f"""
        <div class="weather-widget">
            <div>
                <div style="opacity:0.9">Day {selected_day} 天氣預報</div>
                <div class="weather-temp">{weather_text.split('|')[0]}</div>
            </div>
            <div style="font-size:1.5rem;">{weather_text.split('|')[1]}</div>
        </div>
    """), unsafe_allow_html=True)

    # 編輯模式
    col_t1, col_t2 = st.columns([1, 4])
    is_edit = col_t1.toggle("編輯模式")
    if is_edit and col_t2.button("➕ 新增行程"):
        st.session_state.trip_data[selected_day].append({
            "id": int(time.time()), "time": "12:00", "title": "新景點", "loc": "", "cost": 0, "cat": "spot", "note": "", "trans_mode": "🚗", "trans_min": 30
        })
        st.rerun()

    day_items = sorted(st.session_state.trip_data[selected_day], key=lambda x: x['time'])
    if not day_items:
        st.info("😴 今天還沒有行程")

    for i, item in enumerate(day_items):
        cat_colors = {"food": "#FF8C42", "spot": "#8E2F2F", "trans": "#6c757d", "stay": "#4a4e69", "shop": "#E63946"}
        color = cat_colors.get(item['cat'], "#999")
        
        # 導遊情報
        guide_info = get_ai_guide(item['title'], item['loc'])
        guide_html = ""
        
        # 這裡非常重要：使用了 textwrap.dedent 並移除所有前方縮排
        if guide_info and not is_edit:
            guide_html = textwrap.dedent(f"""
            <div class="guide-box">
                <span class="guide-label">💡 景點攻略：</span> {guide_info['story']} <br>
                <span class="guide-label">🍱 必吃推薦：</span> {guide_info['food']} <br>
                <span class="guide-label">🛍️ 必買清單：</span> {guide_info['buy']}
            </div>
            """)

        nav_btn = f'<a href="{get_nav_link(item["loc"])}" target="_blank" class="nav-btn">🚗 導航</a>' if item['loc'] else ""
        note_text = auto_highlight_text(item['note'])
        note_html = f"<div style='margin-top:8px; color:#666; font-size:0.9rem;'>{note_text}</div>" if item['note'] else ""
        
        # 構建卡片 HTML (確保沒有導致 Code Block 的縮排)
        card_content = textwrap.dedent(f"""
        <div class="app-card">
            <div class="category-strip" style="background-color: {color};"></div>
            <div class="card-header">
                <span class="card-time">{item['time']}</span>
                <span style="font-size:0.9rem; color:{color}; font-weight:bold;">¥{item['cost']:,}</span>
            </div>
            <div class="card-title">{item['title']}</div>
            <div style="font-size:0.9rem; color:#555; margin-bottom:8px;">
                📍 {item['loc'] if item['loc'] else '未設定'} {nav_btn}
            </div>
            {note_html}
            {guide_html}
        </div>
        """)
        
        st.markdown(card_content, unsafe_allow_html=True)

        if is_edit:
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                item['time'] = c1.text_input(f"時間 {i}", item['time'])
                item['title'] = c2.text_input(f"標題 {i}", item['title'])
                item['loc'] = st.text_input(f"地點 {i}", item['loc'])
                item['note'] = st.text_area(f"筆記 {i}", item['note'])
                item['cat'] = st.selectbox(f"類型 {i}", ["spot", "food", "stay", "trans", "shop"], index=["spot", "food", "stay", "trans", "shop"].index(item.get('cat', 'spot')))
                if st.button("🗑️ 刪除", key=f"del_{item['id']}"):
                    st.session_state.trip_data[selected_day].pop(i)
                    st.rerun()

        if i < len(day_items) - 1 and not is_edit:
            st.markdown(f"<div style='margin-left:20px; border-left:2px dashed #ccc; padding-left:15px; color:#888; font-size:0.8rem; padding-bottom:10px;'>⬇️ {item.get('trans_mode','🚗')} 約 {item.get('trans_min', 30)} 分鐘</div>", unsafe_allow_html=True)

# ==========================================
# Tab 2: 地圖路線
# ==========================================
with tab_map:
    st.caption("📍 顯示 Google Maps 路線")
    map_day = st.selectbox("選擇日期", days, key="map_day")
    d_items = sorted(st.session_state.trip_data[map_day], key=lambda x: x['time'])
    locs = [x['loc'] for x in d_items if x['loc']]
    
    if len(locs) > 1:
        origin = urllib.parse.quote(locs[0])
        dest = urllib.parse.quote(locs[-1])
        waypoints = "|".join([urllib.parse.quote(x) for x in locs[1:-1]])
        url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={dest}&waypoints={waypoints}&travelmode=driving"
        st.markdown(f'<a href="{url}" target="_blank" style="display:block; text-align:center; background:#8E2F2F; color:white; padding:12px; border-radius:8px; text-decoration:none;">🗺️ 開啟當日導航路線</a>', unsafe_allow_html=True)
        st.markdown("---")
        for x in d_items:
            st.text(f"{x['time']} - {x['title']}")
    else:
        st.warning("地點不足，無法建立路線。")

# ==========================================
# Tab 3: 重要資訊
# ==========================================
with tab_info:
    st.header("ℹ️ 旅遊重要資訊")

    with st.expander("✈️ 航班 & 🏨 住宿", expanded=True):
        st.markdown("""
        **去程 (星宇 JX821)**: 2026/01/17 10:00 TPE -> 13:30 KIX  
        **回程 (星宇 JX822)**: 2026/01/22 15:00 KIX -> 17:30 TPE
        
        **住宿資訊**:
        *   D1: 白濱萬豪酒店 (訂房號: 882199)
        *   D2-D4: 大阪 Cross Hotel
        """)

    with st.expander("🆘 緊急聯絡電話"):
        st.error("👮 警察 110 | 🚑 救護車 119")
        st.write("台北駐日經濟文化代表處: +81-3-3280-7811")
        st.write("海外急難救助: +886-800-085-095")

    with st.expander("💰 預算概況"):
        total_cost = sum(item['cost'] for day in st.session_state.trip_data.values() for item in day)
        st.metric("總預估花費 (JPY)", f"¥{total_cost:,}", delta="不含機票")

    with st.expander("🧳 行李檢查清單"):
        st.caption("出發前請再次確認")
        for category, items in st.session_state.pack_list.items():
            st.markdown(f"**{category}**")
            cols = st.columns(3)
            for i, (item_name, checked) in enumerate(items.items()):
                is_checked = cols[i % 3].checkbox(item_name, value=checked, key=f"pack_{item_name}")
                st.session_state.pack_list[category][item_name] = is_checked
            st.markdown("---")
            
    st.text_area("📝 臨時備忘錄", placeholder="輸入護照號碼、Wifi密碼等...")