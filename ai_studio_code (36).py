import streamlit as st
import urllib.parse
import time
import re

# -------------------------------------
# 1. 系統設定 & 主題定義
# -------------------------------------
st.set_page_config(page_title="2026 旅程規劃 App", page_icon="🇯🇵", layout="centered", initial_sidebar_state="collapsed")

# 定義主題配色
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
    }
}

# 初始化
if "theme" not in st.session_state: st.session_state.theme = "⛩️ 京都緋紅"
current_theme = THEMES[st.session_state.theme]

# 資料初始化
if "trip_data" not in st.session_state:
    st.session_state.trip_data = {
        1: [
            {"id": 1, "time": "10:00", "title": "關西機場 租車", "loc": "關西機場 Aeroplaza", "cost": 15000, "cat": "trans", "note": "預約代號: 8821", "guide": ""},
            {"id": 2, "time": "12:30", "title": "臨空城 Outlet", "loc": "Rinku Premium Outlets", "cost": 3000, "cat": "food", "note": "必吃 KUA`AINA", "guide": ""},
        ]
    }
if "flight_info" not in st.session_state:
    st.session_state.flight_info = {
        "out_date": "2026/01/17", "out_code": "JX821", "out_time": "10:00", "out_dest": "KIX",
        "in_date": "2026/01/22", "in_code": "JX822", "in_time": "15:00", "in_dest": "TPE"
    }
if "hotel_info" not in st.session_state:
    st.session_state.hotel_info = "Day 1: 白濱萬豪酒店 (訂房號: 8821)\nDay 2-4: 大阪 Cross Hotel (Booking)"
if "contact_info" not in st.session_state:
    st.session_state.contact_info = "警察: 110\n救護車: 119\n駐日代表處: +81-3-3280-7811"

# -------------------------------------
# 2. CSS 樣式 (修復跑版與顏色)
# -------------------------------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    /* 1. 背景與基礎字體 */
    .stApp {{ background-color: {current_theme['bg']} !important; }}
    
    /* 避免使用 div 全域選取器，只針對文字內容 */
    h1, h2, h3, p, li, .stMarkdown, .stRadio label {{ 
        color: {current_theme['text']} !important; 
        font-family: 'Noto Sans TC', sans-serif !important;
    }}
    
    /* 2. 輸入框樣式 */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
        background-color: {current_theme['card']} !important;
        color: {current_theme['text']} !important;
        border: 1px solid {current_theme['secondary']} !important;
    }}
    
    /* 3. 卡片模組 (Card Module) */
    .app-card {{
        background-color: {current_theme['card']};
        border: 1px solid {current_theme['secondary']};
        border-radius: 12px; padding: 16px; margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    
    /* 4. 機票樣式 */
    .flight-ticket {{
        background: {current_theme['card']};
        border: 2px dashed {current_theme['primary']};
        border-radius: 12px; padding: 15px; margin-bottom: 15px;
    }}
    .flight-header {{
        background: {current_theme['primary']}; color: #FFFFFF !important;
        padding: 4px 10px; border-radius: 8px 8px 0 0; font-weight: bold;
        display: inline-block; margin-bottom: 10px;
    }}
    .flight-code {{ font-size: 1.5rem; font-weight: 900; color: {current_theme['primary']} !important; }}
    
    /* 5. 導航按鈕 (地圖頁面專用) */
    .map-btn {{
        display: block; width: 100%; text-align: center;
        background-color: {current_theme['primary']} !important; 
        color: #FFFFFF !important; /* 強制白色字體 */
        padding: 12px; border-radius: 10px; text-decoration: none; 
        margin-bottom: 20px; font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    /* 6. 行程內的小導航按鈕 */
    .nav-btn-small {{
        background: {current_theme['nav_bg']}; color: {current_theme['primary']} !important;
        border: 1px solid {current_theme['primary']}; padding: 2px 10px;
        border-radius: 15px; font-size: 0.75rem; text-decoration: none; margin-left: 8px;
    }}

    /* 7. AI Tag */
    .ai-tag {{ 
        background: {current_theme['primary']}; color: #FFF !important; 
        padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-right:4px;
    }}
    
    /* 8. 修正 Expander 樣式 (避免重疊) */
    .streamlit-expanderHeader {{
        color: {current_theme['text']} !important;
        background-color: transparent !important;
    }}
    </style>
""", unsafe_allow_html=True)

# -------------------------------------
# 3. 邏輯函數
# -------------------------------------
GUIDE_DB = {
    "通用": {"desc": "享受當地的氛圍，別忘了拍照留念！", "food": "便利商店炸雞、季節限定飲料", "buy": "當地明信片"},
    "Outlet": {"desc": "外國遊客憑護照通常有額外折扣。", "food": "Food Court 的漢堡或拉麵", "buy": "運動品牌、日系服飾"},
    "機場": {"desc": "提早2小時抵達，出境後免稅店很好逛。", "food": "機場限定空弁 (便當)", "buy": "白色戀人、東京香蕉"},
    "租車": {"desc": "日本為右駕，轉彎請遵循『左小右大』原則。", "food": "高速公路休息站美食", "buy": "地區限定點心"},
    "貴志": {"desc": "著名的貓站長二代玉值勤中！", "food": "小玉咖啡廳的貓掌甜點", "buy": "貓站長徽章"},
    "白濱": {"desc": "擁有潔白沙灘的溫泉勝地。", "food": "幻之魚「九繪」、海鮮丼", "buy": "紀州梅乾、柚子酒"},
}

def get_guide_html(title, loc, manual_guide):
    """產生導遊 HTML (完全無縮排，防止代碼外洩)"""
    info = None
    # 1. 優先手動
    if manual_guide and manual_guide.strip():
        info = {"desc": manual_guide, "food": "請參考筆記", "buy": "請參考筆記"}
    else:
        # 2. 自動搜尋
        search = (str(title) + str(loc)).lower()
        for k, v in GUIDE_DB.items():
            if k.lower() in search and k != "通用":
                info = v
                break
    
    if info:
        # 這裡使用單行拼接，絕對安全
        return f'<div style="background:{current_theme["bg"]}; border-left:4px solid {current_theme["accent"]}; padding:10px; margin-top:10px; font-size:0.9rem; border-radius:4px;"><b>👨‍🏫 導遊：</b>{info["desc"]}<br><div style="margin-top:4px;"><b>🍱 必吃：</b>{info["food"]}</div><div style="margin-top:2px;"><b>🛍️ 必買：</b>{info["buy"]}</div></div>'
    return ""

def auto_highlight(text):
    if not text: return ""
    text = re.sub(r'(必吃|推薦)', r'<span class="ai-tag">🍱 \1</span>', text)
    text = re.sub(r'(必買|伴手禮)', r'<span class="ai-tag" style="background:#E91E63;">🛍️ \1</span>', text)
    text = re.sub(r'(預約|代號)', r'<span class="ai-tag" style="background:#2196F3;">🎫 \1</span>', text)
    return text

def get_nav_url(loc):
    if not loc: return "#"
    return f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(loc)}&travelmode=driving"

# -------------------------------------
# 4. 主介面
# -------------------------------------
c1, c2 = st.columns([4, 1])
with c1: st.markdown(f"## 2026 阪京自駕遊")
with c2: 
    new_theme = st.selectbox("主題", list(THEMES.keys()), label_visibility="collapsed")
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📅 行程", "🗺️ 地圖", "ℹ️ 資訊"])

# ================= Tab 1: 行程 =================
with tab1:
    days = sorted(st.session_state.trip_data.keys()) or [1]
    
    # 按鈕式天數選擇
    cols = st.columns(len(days))
    if "selected_day" not in st.session_state: st.session_state.selected_day = 1
    
    for i, d in enumerate(days):
        if cols[i].button(f"Day {d}", key=f"dbtn_{d}", use_container_width=True):
            st.session_state.selected_day = d
            
    day = st.session_state.selected_day
    
    # 天氣 Widget (單行 HTML)
    st.markdown(f'<div style="background:linear-gradient(135deg, {current_theme["primary"]}, {current_theme["secondary"]}); padding:15px; border-radius:12px; color:white !important; margin-bottom:15px; display:flex; justify-content:space-between;"><div><b>Day {day} 天氣預報</b><br>🌤️ 12°C 晴時多雲</div><div style="font-size:2rem;">☀️</div></div>', unsafe_allow_html=True)
    
    is_edit = st.toggle("✏️ 編輯/新增")
    if is_edit:
        with st.container(border=True):
            c_a, c_b = st.columns([1, 2])
            n_time = c_a.text_input("時間", "12:00")
            n_title = c_b.text_input("標題", "新景點")
            n_loc = st.text_input("地點 (用於導航/AI)", "")
            if st.button("➕ 加入"):
                if day not in st.session_state.trip_data: st.session_state.trip_data[day] = []
                st.session_state.trip_data[day].append({"id": int(time.time()), "time": n_time, "title": n_title, "loc": n_loc, "cost": 0, "cat": "spot", "note": "", "guide": ""})
                st.rerun()

    # 行程列表
    items = sorted(st.session_state.trip_data.get(day, []), key=lambda x: x['time'])
    for i, item in enumerate(items):
        nav_html = f'<a href="{get_nav_url(item["loc"])}" target="_blank" class="nav-btn-small">🚗 導航</a>' if item["loc"] else ""
        guide_html = get_guide_html(item['title'], item['loc'], item.get('guide', '')) if not is_edit else ""
        note_html = f'<div style="margin-top:6px; font-size:0.9rem; opacity:0.9;">{auto_highlight(item["note"])}</div>'
        
        # 卡片 HTML (單行拼接)
        card_html = f'<div class="app-card"><div style="display:flex; justify-content:space-between; font-weight:bold; margin-bottom:4px;"><span>{item["time"]} {item["title"]}</span><span style="color:{current_theme["primary"]}">¥{item["cost"]:,}</span></div><div style="font-size:0.85rem; color:{current_theme["text"]}; opacity:0.7;">📍 {item["loc"]} {nav_html}</div>{note_html}{guide_html}</div>'
        st.markdown(card_html, unsafe_allow_html=True)
        
        if is_edit:
            with st.expander(f"編輯: {item['title']}"):
                item['time'] = st.text_input(f"時間{item['id']}", item['time'])
                item['title'] = st.text_input(f"標題{item['id']}", item['title'])
                item['loc'] = st.text_input(f"地點{item['id']}", item['loc'])
                item['note'] = st.text_area(f"筆記{item['id']}", item['note'])
                item['guide'] = st.text_area(f"手動導遊{item['id']}", item.get('guide', ''))
                item['cost'] = st.number_input(f"費用{item['id']}", value=item['cost'])
                if st.button(f"刪除{item['id']}"):
                    st.session_state.trip_data[day].pop(i)
                    st.rerun()

# ================= Tab 2: 地圖 =================
with tab2:
    st.caption("🗺️ 視覺化路線")
    m_day = st.selectbox("選擇日期", list(st.session_state.trip_data.keys()), key="m_sel")
    m_items = sorted(st.session_state.trip_data[m_day], key=lambda x: x['time'])
    
    locs = [x['loc'] for x in m_items if x['loc']]
    if len(locs) > 1:
        origin = urllib.parse.quote(locs[0])
        dest = urllib.parse.quote(locs[-1])
        waypoints = "|".join([urllib.parse.quote(x) for x in locs[1:-1]])
        url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={dest}&waypoints={waypoints}&travelmode=driving"
        # 這裡的 class="map-btn" 已經在 CSS 中強制設定為白色字體
        st.markdown(f'<a href="{url}" target="_blank" class="map-btn">🚗 開啟 Google Maps 全程導航</a>', unsafe_allow_html=True)

    # 時間軸
    for item in m_items:
        if not item['loc']: continue
        st.markdown(f"""
        <div style="border-left:3px solid {current_theme['primary']}; margin-left:10px; padding-left:15px; padding-bottom:20px; position:relative;">
            <div style="width:10px; height:10px; background:{current_theme['primary']}; border-radius:50%; position:absolute; left:-6.5px; top:0;"></div>
            <div style="font-weight:bold;">{item['time']} {item['title']}</div>
            <div style="font-size:0.85rem; opacity:0.8;">📍 {item['loc']}</div>
        </div>
        """, unsafe_allow_html=True)

# ================= Tab 3: 資訊 (卡片化) =================
with tab3:
    st.markdown("### ℹ️ 旅遊資訊")
    
    # 1. 航班卡片
    st.markdown(f'<div class="flight-ticket"><div class="flight-header">DEPARTURE 去程</div><div style="display:flex; justify-content:space-between;"><span class="flight-code">{st.session_state.flight_info["out_code"]}</span><div style="text-align:right;"><b>{st.session_state.flight_info["out_time"]}</b><br><span style="font-size:0.8rem;">{st.session_state.flight_info["out_date"]}</span></div></div><div style="margin-top:10px; border-top:1px dashed #ccc;"></div><div style="margin-top:5px; font-size:0.9rem;">TPE 台北 ✈️ {st.session_state.flight_info["out_dest"]} 大阪</div></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div class="flight-ticket"><div class="flight-header">RETURN 回程</div><div style="display:flex; justify-content:space-between;"><span class="flight-code">{st.session_state.flight_info["in_code"]}</span><div style="text-align:right;"><b>{st.session_state.flight_info["in_time"]}</b><br><span style="font-size:0.8rem;">{st.session_state.flight_info["in_date"]}</span></div></div></div>', unsafe_allow_html=True)

    with st.expander("✏️ 編輯航班"):
        c1, c2 = st.columns(2)
        st.session_state.flight_info['out_code'] = c1.text_input("去程班號", st.session_state.flight_info['out_code'])
        st.session_state.flight_info['out_time'] = c2.text_input("去程時間", st.session_state.flight_info['out_time'])
        st.session_state.flight_info['in_code'] = c1.text_input("回程班號", st.session_state.flight_info['in_code'])
        st.session_state.flight_info['in_time'] = c2.text_input("回程時間", st.session_state.flight_info['in_time'])

    # 2. 住宿卡片 (Card Module)
    st.markdown(f'<div style="font-weight:bold; color:{current_theme["primary"]}; margin-top:20px;">🏨 住宿資訊</div>', unsafe_allow_html=True)
    with st.container():
        # 使用自定義 HTML 模擬卡片外框，包裹文字區域
        st.markdown(f'<div class="app-card">', unsafe_allow_html=True)
        st.session_state.hotel_info = st.text_area("住宿詳情 (請輸入)", st.session_state.hotel_info, height=100, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. 緊急聯絡卡片 (Card Module)
    st.markdown(f'<div style="font-weight:bold; color:{current_theme["primary"]}; margin-top:10px;">🆘 緊急聯絡</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown(f'<div class="app-card">', unsafe_allow_html=True)
        st.session_state.contact_info = st.text_area("緊急電話 (請輸入)", st.session_state.contact_info, height=100, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)