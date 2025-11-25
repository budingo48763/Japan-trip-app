import streamlit as st
from datetime import datetime, timedelta
import urllib.parse
import time
import pandas as pd
import re

# -------------------------------------
# 1. 系統設定 & 主題定義
# -------------------------------------
st.set_page_config(page_title="2026 旅程規劃 App", page_icon="✈️", layout="centered", initial_sidebar_state="collapsed")

# 🎨 主題配色庫
THEMES = {
    "⛩️ 京都緋紅 (預設)": {
        "bg": "#FDFCF5", "card": "#FFFFFF", "text": "#2B2B2B", "primary": "#8E2F2F", "secondary": "#D6A6A6", "sub": "#666666",
        "tag_food": "#FF8C42", "tag_buy": "#E63946", "tag_res": "#2A9D8F"
    },
    "🌫️ 莫蘭迪·霧藍": {
        "bg": "#F0F4F8", "card": "#FFFFFF", "text": "#243B53", "primary": "#486581", "secondary": "#BCCCDC", "sub": "#627D98",
        "tag_food": "#D4A373", "tag_buy": "#BC6C25", "tag_res": "#606C38"
    },
    "🌿 莫蘭迪·鼠尾草": {
        "bg": "#F1F5F1", "card": "#FFFFFF", "text": "#2C3E2C", "primary": "#5F7161", "secondary": "#AFC0B0", "sub": "#506050",
        "tag_food": "#DAA520", "tag_buy": "#CD5C5C", "tag_res": "#4682B4"
    },
    "🌑 現代·極簡灰": {
        "bg": "#F5F5F5", "card": "#FFFFFF", "text": "#1A1A1A", "primary": "#333333", "secondary": "#CCCCCC", "sub": "#666666",
        "tag_food": "#555", "tag_buy": "#777", "tag_res": "#000"
    }
}

if "selected_theme_name" not in st.session_state: st.session_state.selected_theme_name = "⛩️ 京都緋紅 (預設)"
current_theme = THEMES[st.session_state.selected_theme_name]

# -------------------------------------
# 2. 核心功能函數 (AI 導遊 & 導航)
# -------------------------------------

# 智能文字分析：將筆記中的關鍵字轉為標籤
def auto_highlight_text(text):
    if not text: return ""
    # 必吃/推薦美食
    text = re.sub(r'(必吃|推薦|名物|招牌)', f'<span class="ai-tag tag-food">🍴 \\1</span>', text)
    # 必買/伴手禮
    text = re.sub(r'(必買|伴手禮|藥妝|限定)', f'<span class="ai-tag tag-buy">🛍️ \\1</span>', text)
    # 預約/代號
    text = re.sub(r'(預約|代號|訂位|門票|整理券)', f'<span class="ai-tag tag-res">🎫 \\1</span>', text)
    # 價格/費用
    text = re.sub(r'(¥\d+|NT\$\d+)', f'<span style="font-weight:bold; color:{current_theme["primary"]};">\\1</span>', text)
    return text

# 生成「駕駛導航」連結 (直接開啟導航模式)
def get_nav_link(location):
    if not location: return "#"
    # travelmode=driving 開啟開車模式, dir_action=navigate 直接進入導航
    return f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(location)}&travelmode=driving&dir_action=navigate"

def get_category_style(cat):
    # 定義左側色條顏色 與 圖示
    styles = {
        "trans": {"color": "#6c757d", "icon": "🚆", "label": "交通"},
        "food":  {"color": current_theme['tag_food'], "icon": "🍱", "label": "美食"},
        "stay":  {"color": "#4a4e69", "icon": "🏨", "label": "住宿"},
        "spot":  {"color": current_theme['primary'], "icon": "⛩️", "label": "景點"},
        "shop":  {"color": current_theme['tag_buy'], "icon": "🛍️", "label": "購物"},
        "other": {"color": current_theme['sub'], "icon": "📍", "label": "其他"}
    }
    return styles.get(cat, styles["other"])

# -------------------------------------
# 3. CSS 樣式 (App-Like UI)
# -------------------------------------
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    .stApp {{ 
        background-color: {current_theme['bg']} !important;
        color: {current_theme['text']} !important; 
        font-family: 'Noto Sans TC', sans-serif !important;
    }}

    /* 隱藏預設元件，營造 App 感 */
    header, footer, [data-testid="stToolbar"] {{ display: none !important; }}
    
    /* ---------------- 卡片設計 ---------------- */
    .app-card {{
        background: {current_theme['card']};
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid rgba(0,0,0,0.02);
        position: relative;
        overflow: hidden;
        transition: transform 0.1s;
    }}
    .app-card:active {{ transform: scale(0.99); }} /* 按壓回饋 */
    
    /* 左側類別色條 */
    .category-strip {{
        position: absolute; left: 0; top: 0; bottom: 0; width: 6px;
    }}

    /* 卡片頭部 */
    .card-header {{
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 8px;
    }}
    .card-time {{
        font-family: 'Roboto', sans-serif; font-weight: 700; font-size: 1.1rem;
        color: {current_theme['text']};
    }}
    .card-cat-icon {{ font-size: 0.9rem; opacity: 0.8; margin-right: 4px; }}

    /* 卡片標題與內容 */
    .card-title {{
        font-size: 1.15rem; font-weight: 700; color: {current_theme['text']};
        margin-bottom: 6px; line-height: 1.3;
    }}
    .card-loc {{
        font-size: 0.85rem; color: {current_theme['sub']};
        display: flex; align-items: center; margin-bottom: 10px;
    }}
    
    /* 導航按鈕 (右浮動或獨立區塊) */
    .nav-btn {{
        background-color: {current_theme['bg']}; color: {current_theme['primary']};
        border: 1px solid {current_theme['primary']};
        padding: 6px 14px; border-radius: 20px;
        font-size: 0.8rem; font-weight: bold;
        text-decoration: none; display: inline-flex; align-items: center; gap: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .nav-btn:hover {{ background-color: {current_theme['primary']}; color: #FFF; }}

    /* AI 標籤樣式 */
    .ai-tag {{
        display: inline-block; padding: 2px 8px; border-radius: 4px;
        font-size: 0.75rem; font-weight: bold; margin-right: 4px; margin-bottom: 2px;
        color: white; box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }}
    .tag-food {{ background-color: {current_theme['tag_food']}; }}
    .tag-buy {{ background-color: {current_theme['tag_buy']}; }}
    .tag-res {{ background-color: {current_theme['tag_res']}; }}
    
    .card-note {{
        font-size: 0.9rem; color: {current_theme['sub']};
        background: {current_theme['bg']}; padding: 8px; border-radius: 8px;
        margin-top: 8px; line-height: 1.5;
    }}

    /* 交通連接線 */
    .trans-connector {{
        margin-left: 20px; border-left: 2px dashed {current_theme['secondary']};
        padding-left: 15px; padding-top: 5px; padding-bottom: 15px;
        font-size: 0.8rem; color: {current_theme['sub']}; font-weight: bold;
    }}

    /* 天氣 Widget */
    .weather-widget {{
        background: linear-gradient(135deg, {current_theme['primary']} 0%, {current_theme['secondary']} 100%);
        color: white; border-radius: 16px; padding: 15px 20px;
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }}
    .weather-temp {{ font-size: 2rem; font-weight: 700; line-height: 1; }}
    .weather-info {{ font-size: 0.9rem; opacity: 0.9; }}

    /* Tab 優化 */
    div[data-baseweb="tab-list"] {{
        background: {current_theme['bg']}; position: sticky; top: 0; z-index: 100;
        padding-top: 10px; padding-bottom: 5px;
    }}
    button[data-baseweb="tab"] {{
        flex: 1; border-bottom: 2px solid transparent; padding: 10px 0;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        border-bottom: 3px solid {current_theme['primary']};
        color: {current_theme['primary']}; font-weight: bold;
    }}

    /* 輸入框優化 */
    .stTextInput input, .stNumberInput input, .stTimeInput input {{
        background: {current_theme['card']}; border: 1px solid #EEE; border-radius: 8px;
    }}
    </style>
""", unsafe_allow_html=True)

# -------------------------------------
# 4. 資料初始化
# -------------------------------------
if "trip_title" not in st.session_state: st.session_state.trip_title = "2026 阪京自駕遊"
if "exchange_rate" not in st.session_state: st.session_state.exchange_rate = 0.215
if "trip_days_count" not in st.session_state: st.session_state.trip_days_count = 5
if "trip_data" not in st.session_state:
    # 初始化範例資料
    st.session_state.trip_data = {
        1: [
            {"id": 101, "time": "10:00", "title": "關西機場 租車", "loc": "關西國際機場 租車櫃台", "cost": 15000, "cat": "trans", "note": "預約代號：KIX-8821。記得檢查車況、拿ETC卡。", "expenses": [], "trans_mode": "🚗 自駕", "trans_min": 75},
            {"id": 102, "time": "12:30", "title": "臨空城 Outlet 午餐", "loc": "Rinku Premium Outlets", "cost": 3000, "cat": "food", "note": "必吃 KUA`AINA 漢堡。順便買 Nike 運動鞋。", "expenses": [], "trans_mode": "🚗 自駕", "trans_min": 60},
            {"id": 103, "time": "15:00", "title": "和歌山 貴志車站", "loc": "貴志駅", "cost": 0, "cat": "spot", "note": "來看貓站長，記得買貓咪周邊伴手禮。", "expenses": [], "trans_mode": "🚗 自駕", "trans_min": 90},
            {"id": 104, "time": "18:00", "title": "白濱溫泉 飯店 Check-in", "loc": "白濱萬豪酒店", "cost": 0, "cat": "stay", "note": "享受海景溫泉。", "expenses": [], "trans_mode": "📍 休息", "trans_min": 0}
        ]
    }
    # 補齊其他天數
    for d in range(2, 6): st.session_state.trip_data[d] = []

if "flight_info" not in st.session_state:
    st.session_state.flight_info = {"out": {"date": "2026/1/17", "code": "JX821", "time": "10:00"}, "in": {"date": "2026/1/22", "code": "JX822", "time": "15:00"}}

# -------------------------------------
# 5. 主程式介面
# -------------------------------------

# 頂部標題與編輯按鈕 (極簡化)
c_head1, c_head2 = st.columns([5, 1])
with c_head1:
    st.markdown(f"<div style='font-size:1.5rem; font-weight:900;'>{st.session_state.trip_title}</div>", unsafe_allow_html=True)
with c_head2:
    with st.popover("⚙️"):
        st.markdown("**設定**")
        st.session_state.trip_title = st.text_input("旅程名稱", st.session_state.trip_title)
        st.session_state.exchange_rate = st.number_input("匯率", value=st.session_state.exchange_rate, format="%.3f")
        theme_name = st.selectbox("主題配色", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.selected_theme_name))
        if theme_name != st.session_state.selected_theme_name:
            st.session_state.selected_theme_name = theme_name
            st.rerun()

# 分頁導航
tab1, tab2, tab3 = st.tabs(["📅 行程", "🗺️ 地圖", "🧰 工具箱"])

# ==========================================
# Tab 1: 每日行程 (App 核心)
# ==========================================
with tab1:
    # 日期選擇器 (橫向滑動感)
    days = list(range(1, st.session_state.trip_days_count + 1))
    selected_day = st.radio("選擇天數", days, horizontal=True, label_visibility="collapsed", format_func=lambda x: f"D{x}")
    
    # 獲取當日資料
    day_items = st.session_state.trip_data.get(selected_day, [])
    day_items.sort(key=lambda x: x['time'])
    
    # --- 天氣 Widget (模擬) ---
    # 在實際應用中，這裡可以接 API，現在用模擬資料讓用戶體驗 UI
    weather_map = {1: ("🌤️ 晴時多雲", "12°C", "適合自駕"), 2: ("🌧️ 短暫雨", "10°C", "記得帶傘"), 3: ("☁️ 陰天", "11°C", "舒適")}
    w_desc, w_temp, w_tip = weather_map.get(selected_day % 3 + 1, ("☀️ 晴朗", "14°C", "注意防曬"))
    
    st.markdown(f"""
        <div class="weather-widget">
            <div>
                <div style="font-size:0.9rem;">Day {selected_day} 天氣預報</div>
                <div class="weather-temp">{w_temp} {w_desc.split(' ')[0]}</div>
                <div class="weather-info">{w_desc.split(' ')[1] if ' ' in w_desc else w_desc} | {w_tip}</div>
            </div>
            <div style="text-align:right; opacity:0.8;">
                <div style="font-size:2rem;">{w_desc.split(' ')[0]}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 編輯模式開關 ---
    col_tools_1, col_tools_2 = st.columns([1, 4])
    with col_tools_1:
        is_edit = st.toggle("編輯", key="edit_mode")
    with col_tools_2:
        if is_edit:
            if st.button("➕ 新增", use_container_width=True):
                st.session_state.trip_data[selected_day].append({
                    "id": int(time.time()), "time": "12:00", "title": "新行程", "loc": "", 
                    "cost": 0, "cat": "spot", "note": "", "expenses": [], "trans_mode": "🚗 自駕", "trans_min": 30
                })
                st.rerun()

    # --- 行程卡片渲染 ---
    if not day_items:
        st.info("😴 本日尚無行程，點擊「編輯」開始規劃。")

    for i, item in enumerate(day_items):
        style = get_category_style(item['cat'])
        nav_url = get_nav_link(item['loc'])
        
        # 處理費用顯示
        cost_html = ""
        if item['cost'] > 0:
            twd = int(item['cost'] * st.session_state.exchange_rate)
            cost_html = f"<span style='float:right; font-weight:bold; color:{current_theme['primary']}; font-size:0.9rem;'>¥{item['cost']:,} (NT${twd:,})</span>"

        # 處理 AI 筆記標記
        note_display = auto_highlight_text(item['note'])
        
        # 導航按鈕 HTML
        nav_btn_html = ""
        if item['loc']:
            nav_btn_html = f'<a href="{nav_url}" target="_blank" class="nav-btn">🚗 導航</a>'

        # 卡片 HTML
        card_html = f"""
        <div class="app-card">
            <div class="category-strip" style="background-color: {style['color']};"></div>
            <div class="card-header">
                <div class="card-time">{item['time']} <span style="font-weight:normal; font-size:0.9rem; color:#888;">{style['icon']} {style['label']}</span></div>
                {cost_html}
            </div>
            <div class="card-title">{item['title']}</div>
            <div class="card-loc">
                <span style="margin-right:8px;">📍 {item['loc'] if item['loc'] else '未設定地點'}</span>
                {nav_btn_html}
            </div>
            {f'<div class="card-note">{note_display}</div>' if item['note'] and not is_edit else ''}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        # 編輯介面 (僅在編輯模式顯示)
        if is_edit:
            with st.container(border=True):
                c1, c2 = st.columns([1, 1])
                item['time'] = c1.text_input("時間", item['time'], key=f"t_{item['id']}")
                item['cat'] = c2.selectbox("類型", ["spot","food","shop","stay","trans","other"], key=f"cat_{item['id']}")
                item['title'] = st.text_input("標題", item['title'], key=f"ti_{item['id']}")
                item['loc'] = st.text_input("地點 (Google Map 關鍵字)", item['loc'], key=f"lo_{item['id']}")
                item['note'] = st.text_area("筆記 (寫下必吃、預約代號)", item['note'], key=f"no_{item['id']}")
                c3, c4 = st.columns(2)
                item['cost'] = c3.number_input("預算(日幣)", value=item['cost'], step=1000, key=f"co_{item['id']}")
                if c4.button("🗑️ 刪除", key=f"del_{item['id']}"):
                    st.session_state.trip_data[selected_day].pop(i)
                    st.rerun()

        # 交通連接線 (除了最後一個行程)
        if i < len(day_items) - 1:
            next_item = day_items[i+1]
            trans_mode = item.get('trans_mode', '🚗 自駕')
            trans_min = item.get('trans_min', 30)
            
            if is_edit:
                 st.markdown(f"<div class='trans-connector'>⬇️ 移動設定</div>", unsafe_allow_html=True)
                 ct1, ct2 = st.columns(2)
                 item['trans_mode'] = ct1.selectbox("方式", ["🚗 自駕", "🚆 電車", "🚶 步行"], key=f"tm_{item['id']}")
                 item['trans_min'] = ct2.number_input("分鐘", value=trans_min, step=5, key=f"tmin_{item['id']}")
            else:
                st.markdown(f"""
                <div class="trans-connector">
                    {trans_mode} 約 {trans_min} 分鐘
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# Tab 2: 地圖路線
# ==========================================
with tab2:
    st.markdown("### 🗺️ 當日路線全覽")
    map_day = st.selectbox("查看哪一天的路線?", days, format_func=lambda x: f"Day {x}")
    d_items = sorted(st.session_state.trip_data[map_day], key=lambda x: x['time'])
    valid_locs = [x['loc'] for x in d_items if x['loc']]
    
    if len(valid_locs) > 1:
        # 生成 Google Maps 路線連結
        origin = valid_locs[0]
        dest = valid_locs[-1]
        waypoints = "|".join(valid_locs[1:-1])
        gmap_url = f"https://www.google.com/maps/dir/?api=1&origin={urllib.parse.quote(origin)}&destination={urllib.parse.quote(dest)}&waypoints={urllib.parse.quote(waypoints)}&travelmode=driving"
        
        st.success(f"📍 共 {len(valid_locs)} 個地點")
        st.markdown(f"""
        <a href="{gmap_url}" target="_blank" style="
            display:block; width:100%; text-align:center; background:{current_theme['primary']}; 
            color:white; padding:15px; border-radius:12px; text-decoration:none; font-weight:bold; margin-top:10px;">
            🚗 開啟 Google Maps 路線導航
        </a>
        """, unsafe_allow_html=True)
        
        # 簡單的時間軸顯示
        st.markdown("---")
        for item in d_items:
            st.markdown(f"**{item['time']}** {item['title']}")
            if item['loc']:
                st.caption(f"📍 {item['loc']}")
                
    else:
        st.warning("請至少輸入兩個地點以生成路線。")

# ==========================================
# Tab 3: 工具箱 (整合資訊)
# ==========================================
with tab3:
    st.markdown("### 🧰 旅行工具箱")
    
    # 1. 預算統計
    with st.expander("💰 預算與支出", expanded=True):
        total_budget = 0
        total_expense = 0
        
        # 簡單計算邏輯
        for d in st.session_state.trip_data:
            for it in st.session_state.trip_data[d]:
                total_budget += it['cost']
                # 這裡假設如果有 expenses 陣列則是實際支出，否則用預算當預估
                if it['expenses']:
                    total_expense += sum(e['price'] for e in it['expenses'])
        
        c_b1, c_b2 = st.columns(2)
        twd_budget = int(total_budget * st.session_state.exchange_rate)
        c_b1.metric("總預算 (JPY)", f"¥{total_budget:,}", f"NT${twd_budget:,}")
        c_b2.metric("匯率設定", f"{st.session_state.exchange_rate}")
        
        st.markdown("---")
        st.caption("記帳功能請在每日行程的編輯模式中添加明細。")

    # 2. 航班資訊
    with st.expander("✈️ 航班資訊"):
        f_out = st.session_state.flight_info['out']
        f_in = st.session_state.flight_info['in']
        
        st.markdown(f"**去程** {f_out['date']} | {f_out['code']}")
        st.info(f"🕒 {f_out['time']} 出發")
        st.markdown(f"**回程** {f_in['date']} | {f_in['code']}")
        st.info(f"🕒 {f_in['time']} 出發")
        
        if st.checkbox("編輯航班"):
            c1, c2 = st.columns(2)
            st.session_state.flight_info['out']['code'] = c1.text_input("去程班號", f_out['code'])
            st.session_state.flight_info['out']['time'] = c2.text_input("去程時間", f_out['time'])

    # 3. 住宿資訊
    with st.expander("🏨 住宿清單"):
        if "hotel_info" not in st.session_state:
            st.session_state.hotel_info = [{"name": "大阪相鐵飯店", "addr": "大阪市..."}]
        
        for h in st.session_state.hotel_info:
            st.markdown(f"**{h['name']}**")
            st.caption(f"📍 {h['addr']}")
            st.markdown(f"[開啟地圖]({get_nav_link(h['addr'])})")
            st.divider()

    # 4. 緊急聯絡
    with st.expander("🚑 緊急聯絡 (SOS)"):
        st.error("**日本報警：110 | 救護車：119**")
        st.markdown("""
        *   **台北駐日經濟文化代表處**：+81-3-3280-7811
        *   **外交部旅外國人急難救助**：+886-800-085-095
        *   **遺失護照**：請至當地警察署報失後，前往代表處補辦。
        """)

# -------------------------------------
# 結束
# -------------------------------------