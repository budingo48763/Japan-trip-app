import streamlit as st
import urllib.parse
import time
import re

# -------------------------------------
# 1. 系統設定 & 主題定義
# -------------------------------------
st.set_page_config(page_title="2026 旅程規劃 App", page_icon="✈️", layout="centered", initial_sidebar_state="collapsed")

# 定義主題配色 (包含文字顏色與背景，確保對比度)
THEMES = {
    "⛩️ 京都緋紅": {
        "bg": "#FDFCF5", "card": "#FFFFFF", "text": "#2B2B2B", "primary": "#8E2F2F", "secondary": "#D6A6A6", 
        "accent": "#FFC107", "nav_bg": "#FFE0E0"
    },
    "🌊 鎌倉海藍": {
        "bg": "#F0F8FF", "card": "#FFFFFF", "text": "#1A237E", "primary": "#304FFE", "secondary": "#C5CAE9", 
        "accent": "#00BCD4", "nav_bg": "#E8EAF6"
    },
    "🍵 宇治抹茶": {
        "bg": "#F1F8E9", "card": "#FFFFFF", "text": "#33691E", "primary": "#558B2F", "secondary": "#DCEDC8", 
        "accent": "#AED581", "nav_bg": "#F1F8E9"
    },
    "🌑 東京夜黑": {
        "bg": "#121212", "card": "#1E1E1E", "text": "#E0E0E0", "primary": "#BB86FC", "secondary": "#333333", 
        "accent": "#03DAC6", "nav_bg": "#2C2C2C"
    }
}

# 初始化 Session State (確保資料可編輯)
if "theme" not in st.session_state: st.session_state.theme = "⛩️ 京都緋紅"
if "flight_info" not in st.session_state:
    st.session_state.flight_info = {
        "out_date": "2026/01/17", "out_code": "JX821", "out_time": "10:00", "out_dest": "KIX",
        "in_date": "2026/01/22", "in_code": "JX822", "in_time": "15:00", "in_dest": "TPE"
    }
if "hotel_info" not in st.session_state:
    st.session_state.hotel_info = "Day 1: 白濱萬豪酒店 (訂房號: 8821)\nDay 2-4: 大阪 Cross Hotel (Booking)"
if "contact_info" not in st.session_state:
    st.session_state.contact_info = "警察: 110\n救護車: 119\n駐日代表處: +81-3-3280-7811"

# 取得當前主題
current_theme = THEMES[st.session_state.theme]

# -------------------------------------
# 2. CSS 動態樣式注入
# -------------------------------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    /* 全域設定 */
    .stApp {{ background-color: {current_theme['bg']} !important; }}
    
    /* 強制文字顏色 */
    h1, h2, h3, p, div, span, label, li {{ 
        color: {current_theme['text']} !important; 
        font-family: 'Noto Sans TC', sans-serif !important;
    }}
    
    /* 輸入框樣式 */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
        background-color: {current_theme['card']} !important;
        color: {current_theme['text']} !important;
        border: 1px solid {current_theme['secondary']} !important;
    }}
    
    /* 行程卡片 */
    .app-card {{
        background-color: {current_theme['card']};
        border: 1px solid {current_theme['secondary']};
        border-radius: 16px; padding: 16px; margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        position: relative;
    }}
    
    /* 機票樣式 (Flight Ticket) */
    .flight-ticket {{
        background: {current_theme['card']};
        border: 2px dashed {current_theme['primary']};
        border-radius: 12px; padding: 15px; margin-bottom: 15px;
        position: relative;
    }}
    .flight-header {{
        background: {current_theme['primary']}; color: #FFF !important;
        padding: 4px 10px; border-radius: 8px 8px 0 0; font-weight: bold;
        display: inline-block; margin-bottom: 10px;
    }}
    .flight-row {{ display: flex; justify-content: space-between; align-items: center; }}
    .flight-code {{ font-size: 1.5rem; font-weight: 900; color: {current_theme['primary']} !important; }}
    
    /* 導航按鈕 */
    .nav-btn {{
        background: {current_theme['nav_bg']}; color: {current_theme['primary']} !important;
        border: 1px solid {current_theme['primary']}; padding: 4px 12px;
        border-radius: 20px; font-size: 0.8rem; text-decoration: none; display: inline-block;
    }}

    /* 地圖時間軸樣式 */
    .map-timeline-item {{
        border-left: 3px solid {current_theme['primary']};
        margin-left: 10px; padding-left: 20px; padding-bottom: 20px; position: relative;
    }}
    .map-timeline-dot {{
        width: 12px; height: 12px; background: {current_theme['primary']};
        border-radius: 50%; position: absolute; left: -7.5px; top: 0;
    }}
    
    /* AI Tag */
    .ai-tag {{ 
        background: {current_theme['primary']}; color: #FFF !important; 
        padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; 
    }}
    </style>
""", unsafe_allow_html=True)

# -------------------------------------
# 3. 智能導遊邏輯 (擴充版)
# -------------------------------------
# 擴充關鍵字庫，讓它變聰明
GUIDE_DB = {
    "通用": {"desc": "享受當地的氛圍，別忘了拍照留念！", "food": "便利商店炸雞、季節限定飲料", "buy": "當地明信片"},
    "Outlet": {"desc": "準備好你的信用卡，通常外國遊客憑護照有額外折扣。", "food": "Food Court 的漢堡或拉麵", "buy": "運動品牌、日系服飾"},
    "機場": {"desc": "提早2小時抵達，出境後免稅店很好逛。", "food": "機場限定空弁 (便當)", "buy": "白色戀人、東京香蕉"},
    "神社": {"desc": "參拜前記得在手水舍洗手漱口，二禮二拍手一禮。", "food": "參道上的烤糰子、抹茶冰淇淋", "buy": "御守 (交通安全/戀愛成就)"},
    "寺": {"desc": "感受寂靜與禪意，注意部分區域禁止攝影。", "food": "湯豆腐、精進料理 (素食)", "buy": "線香、朱印帳"},
    "溫泉": {"desc": "入浴前請先沖洗身體，刺青者請先確認規定。", "food": "溫泉饅頭、泡完後的咖啡牛奶", "buy": "入浴劑、溫泉保養品"},
    "車站": {"desc": "日本車站通常連通百貨公司，非常便利。", "food": "站立食拉麵、鐵路便當", "buy": "地區限定伴手禮"},
    "烤肉": {"desc": "日本國產牛非常美味，建議點牛舌做開場。", "food": "上等牛五花、橫膈膜", "buy": "燒肉醬"},
    "拉麵": {"desc": "吃麵發出聲音代表好吃，不用感到害羞。", "food": "替玉 (加麵)、半熟蛋", "buy": "店家推出的快煮麵包"},
    # 特定地點
    "貴志": {"desc": "著名的貓站長二代玉值勤中！車站也是貓臉造型。", "food": "小玉咖啡廳的貓掌甜點", "buy": "貓站長徽章、和歌山橘子汁"},
    "白濱": {"desc": "擁有潔白沙灘的溫泉勝地。", "food": "幻之魚「九繪」、海鮮丼", "buy": "紀州梅乾、柚子酒"},
}

def get_guide_info(title, loc, manual_guide=None):
    """
    1. 優先顯示使用者手動輸入的導遊資訊
    2. 自動根據關鍵字匹配
    """
    if manual_guide and manual_guide.strip():
        return {"desc": manual_guide, "food": "請參考筆記", "buy": "請參考筆記"}

    search_text = (str(title) + str(loc)).lower()
    
    # 搜尋特定關鍵字
    for key, info in GUIDE_DB.items():
        if key.lower() in search_text and key != "通用":
            return info
            
    # 如果找不到，回傳通用建議 (不顯示空白)
    return None

def auto_highlight(text):
    if not text: return ""
    text = re.sub(r'(必吃|推薦)', r'<span class="ai-tag">🍱 \1</span>', text)
    text = re.sub(r'(必買|伴手禮)', r'<span class="ai-tag" style="background:#E91E63;">🛍️ \1</span>', text)
    return text

def get_nav_link(loc):
    if not loc: return "#"
    return f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(loc)}&travelmode=driving"

# -------------------------------------
# 4. 資料初始化
# -------------------------------------
if "trip_data" not in st.session_state:
    st.session_state.trip_data = {
        1: [
            {"id": 1, "time": "10:00", "title": "關西機場 租車", "loc": "關西機場 Aeroplaza", "cost": 15000, "cat": "trans", "note": "預約代號: 8821", "guide": ""},
            {"id": 2, "time": "12:30", "title": "臨空城 Outlet", "loc": "Rinku Premium Outlets", "cost": 3000, "cat": "food", "note": "必吃 KUA`AINA", "guide": ""},
        ]
    }

# -------------------------------------
# 5. 主程式介面
# -------------------------------------
c1, c2 = st.columns([4, 1])
with c1: st.markdown(f"## 2026 阪京自駕遊 {st.session_state.theme.split(' ')[0]}")
with c2: 
    new_theme = st.selectbox("主題", list(THEMES.keys()), label_visibility="collapsed")
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📅 行程", "🗺️ 地圖", "ℹ️ 資訊(可編輯)"])

# ================= Tab 1: 每日行程 =================
with tab1:
    days = sorted(st.session_state.trip_data.keys())
    if not days: days = [1]
    
    # 天數選擇 (按鈕樣式)
    col_days = st.columns(len(days) + 1)
    selected_day = 1
    for idx, d in enumerate(days):
        if col_days[idx].button(f"Day {d}", use_container_width=True, key=f"btn_d{d}"):
            st.session_state.selected_day = d
    
    if "selected_day" not in st.session_state: st.session_state.selected_day = 1
    current_day = st.session_state.selected_day
    
    # 天氣 Widget
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, {current_theme['primary']}, {current_theme['secondary']}); 
         padding:15px; border-radius:12px; color:white !important; margin-bottom:15px; display:flex; justify-content:space-between;">
        <div><b>Day {current_day} 天氣預報</b><br>🌤️ 12°C | 晴時多雲</div>
        <div style="font-size:2rem;">☀️</div>
    </div>
    """, unsafe_allow_html=True)

    # 編輯模式開關
    is_edit = st.toggle("✏️ 編輯行程 / 新增景點")
    
    if is_edit:
        with st.container(border=True):
            st.caption("新增行程")
            c_new1, c_new2 = st.columns([1, 2])
            new_time = c_new1.text_input("時間", "12:00")
            new_title = c_new2.text_input("標題", "新景點")
            new_loc = st.text_input("地點 (用於導航與AI導遊)", "")
            if st.button("➕ 加入清單"):
                if current_day not in st.session_state.trip_data: st.session_state.trip_data[current_day] = []
                st.session_state.trip_data[current_day].append({
                    "id": int(time.time()), "time": new_time, "title": new_title, 
                    "loc": new_loc, "cost": 0, "cat": "spot", "note": "", "guide": ""
                })
                st.rerun()

    # 顯示行程
    items = st.session_state.trip_data.get(current_day, [])
    items.sort(key=lambda x: x['time'])
    
    for i, item in enumerate(items):
        # 導遊邏輯：優先用手動 guide，沒有則自動搜尋
        guide_data = get_guide_info(item['title'], item['loc'], item.get('guide', ''))
        
        # 卡片 HTML
        nav_html = f'<a href="{get_nav_link(item["loc"])}" target="_blank" class="nav-btn">🚗 導航</a>' if item["loc"] else ""
        note_html = f'<div style="color:{current_theme["text"]}; opacity:0.8; font-size:0.9rem; margin-top:5px;">{auto_highlight(item["note"])}</div>'
        
        guide_html = ""
        if guide_data and not is_edit:
            guide_html = f"""
            <div style="background:{current_theme['bg']}; border-left:4px solid {current_theme['accent']}; padding:8px; margin-top:10px; font-size:0.85rem; border-radius:4px;">
                <b>👨‍🏫 導遊：</b>{guide_data['desc']}<br>
                <b>🍱 必吃：</b>{guide_data['food']} | <b>🛍️ 必買：</b>{guide_data['buy']}
            </div>
            """

        st.markdown(f"""
        <div class="app-card">
            <div style="display:flex; justify-content:space-between; font-weight:bold; margin-bottom:5px;">
                <span>{item['time']} {item['title']}</span>
                <span style="color:{current_theme['primary']}">¥{item['cost']:,}</span>
            </div>
            <div style="font-size:0.85rem; opacity:0.7;">📍 {item['loc']} {nav_html}</div>
            {note_html}
            {guide_html}
        </div>
        """, unsafe_allow_html=True)
        
        # 編輯區 (展開式)
        if is_edit:
            with st.expander(f"編輯: {item['title']}"):
                item['time'] = st.text_input("時間", item['time'], key=f"t{item['id']}")
                item['title'] = st.text_input("標題", item['title'], key=f"ti{item['id']}")
                item['loc'] = st.text_input("地點 (更改觸發導遊)", item['loc'], key=f"l{item['id']}")
                item['cost'] = st.number_input("費用", value=item['cost'], key=f"c{item['id']}")
                item['note'] = st.text_area("筆記", item['note'], key=f"n{item['id']}")
                # 新增：手動導遊介紹
                item['guide'] = st.text_area("自訂導遊介紹 (留空則自動偵測)", item.get('guide', ''), key=f"g{item['id']}")
                if st.button("🗑️ 刪除", key=f"d{item['id']}"):
                    st.session_state.trip_data[current_day].pop(i)
                    st.rerun()

# ================= Tab 2: 地圖動態時間軸 =================
with tab2:
    st.caption("🗺️ 視覺化路線")
    map_day = st.selectbox("選擇日期", list(st.session_state.trip_data.keys()), key="map_select")
    m_items = sorted(st.session_state.trip_data[map_day], key=lambda x: x['time'])
    
    # 產生 Google Map 全程連結
    locs = [x['loc'] for x in m_items if x['loc']]
    if len(locs) > 1:
        origin = urllib.parse.quote(locs[0])
        dest = urllib.parse.quote(locs[-1])
        waypoints = "|".join([urllib.parse.quote(x) for x in locs[1:-1]])
        url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={dest}&waypoints={waypoints}&travelmode=driving"
        st.markdown(f"""
        <a href="{url}" target="_blank" style="display:block; text-align:center; background:{current_theme['primary']}; 
           color:white !important; padding:12px; border-radius:10px; text-decoration:none; margin-bottom:20px; font-weight:bold;">
           🚗 開啟 Google Maps 全程導航
        </a>
        """, unsafe_allow_html=True)
    
    # 時間軸 UI
    for item in m_items:
        if not item['loc']: continue
        st.markdown(f"""
        <div class="map-timeline-item">
            <div class="map-timeline-dot"></div>
            <div style="font-weight:bold; font-size:1.1rem;">{item['time']} {item['title']}</div>
            <div style="color:{current_theme['text']}; opacity:0.8; font-size:0.9rem;">📍 {item['loc']}</div>
            <a href="{get_nav_link(item['loc'])}" target="_blank" 
               style="font-size:0.8rem; color:{current_theme['primary']} !important; text-decoration:underline;">
               單點導航 >
            </a>
        </div>
        """, unsafe_allow_html=True)

# ================= Tab 3: 重要資訊 (可編輯 & 機票樣式) =================
with tab3:
    st.markdown("### ℹ️ 旅遊資訊 (可編輯)")
    
    # 機票樣式區塊
    st.markdown(f'<div style="font-weight:bold; color:{current_theme["primary"]}; margin-bottom:5px;">✈️ 航班資訊</div>', unsafe_allow_html=True)
    
    # 去程
    with st.container():
        st.markdown(f"""
        <div class="flight-ticket">
            <div class="flight-header">DEPARTURE 去程</div>
            <div class="flight-row">
                <div class="flight-code">{st.session_state.flight_info['out_code']}</div>
                <div style="text-align:right;">
                    <div style="font-size:1.2rem; font-weight:bold;">{st.session_state.flight_info['out_time']}</div>
                    <div style="font-size:0.8rem;">{st.session_state.flight_info['out_date']}</div>
                </div>
            </div>
            <div style="border-top:1px dashed #ccc; margin:10px 0;"></div>
            <div style="display:flex; justify-content:space-between; font-size:0.9rem;">
                <span>TPE 台北</span> ✈️ <span>{st.session_state.flight_info['out_dest']} 大阪</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("✏️ 編輯航班"):
            c1, c2 = st.columns(2)
            st.session_state.flight_info['out_code'] = c1.text_input("去程班號", st.session_state.flight_info['out_code'])
            st.session_state.flight_info['out_time'] = c2.text_input("去程時間", st.session_state.flight_info['out_time'])
            st.session_state.flight_info['out_date'] = st.text_input("去程日期", st.session_state.flight_info['out_date'])

    # 回程 (簡化顯示，可依樣畫葫蘆)
    st.markdown(f"""
    <div class="flight-ticket">
        <div class="flight-header">RETURN 回程</div>
        <div class="flight-row">
            <div class="flight-code">{st.session_state.flight_info['in_code']}</div>
            <div style="text-align:right;">
                <div style="font-size:1.2rem; font-weight:bold;">{st.session_state.flight_info['in_time']}</div>
                <div style="font-size:0.8rem;">{st.session_state.flight_info['in_date']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 住宿資訊 (文字框編輯)
    st.markdown(f'<div style="font-weight:bold; color:{current_theme["primary"]}; margin-top:20px;">🏨 住宿資訊</div>', unsafe_allow_html=True)
    st.session_state.hotel_info = st.text_area("住宿詳情", st.session_state.hotel_info, height=100)
    
    # 緊急聯絡 (文字框編輯)
    st.markdown(f'<div style="font-weight:bold; color:{current_theme["primary"]}; margin-top:20px;">🆘 緊急聯絡</div>', unsafe_allow_html=True)
    st.session_state.contact_info = st.text_area("緊急電話", st.session_state.contact_info, height=100)