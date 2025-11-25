import streamlit as st
import urllib.parse
import time
import re

# -------------------------------------
# 1. 系統設定 & CSS 強制樣式 (修復深色模式與跑版)
# -------------------------------------
st.set_page_config(page_title="2026 阪京自駕遊", page_icon="🇯🇵", layout="centered", initial_sidebar_state="collapsed")

# 強制配色變數
BG_COLOR = "#F9F9F9"
CARD_COLOR = "#FFFFFF"
TEXT_COLOR = "#000000"
PRIMARY_COLOR = "#8E2F2F"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    
    /* 1. 全域強制白底黑字 (解決手機深色模式問題) */
    .stApp {{
        background-color: {BG_COLOR} !important;
        font-family: 'Noto Sans TC', sans-serif !important;
    }}
    
    p, div, span, label, h1, h2, h3, li {{
        color: {TEXT_COLOR} !important;
    }}

    /* 2. 輸入框強制樣式 (解決輸入框看不到字的問題) */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
        background-color: #EEEEEE !important; 
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
    }}
    
    /* 3. Radio Button 優化 (變身為按鈕樣式，解決跑版) */
    .stRadio div[role="radiogroup"] {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        flex-direction: row;
    }}
    .stRadio div[role="radiogroup"] label {{
        background-color: #FFFFFF !important;
        border: 1px solid #DDDDDD !important;
        padding: 8px 16px !important;
        border-radius: 20px !important;
        margin-right: 0px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    /* 被選中的項目 */
    .stRadio div[role="radiogroup"] label[data-checked="true"] {{
        background-color: {PRIMARY_COLOR} !important;
        color: white !important;
        border-color: {PRIMARY_COLOR} !important;
    }}
    /* 選中時內部的文字變白 */
    .stRadio div[role="radiogroup"] label[data-checked="true"] p {{
        color: white !important;
    }}

    /* 4. 隱藏多餘元件 */
    header, footer, [data-testid="stToolbar"] {{ display: none !important; }}

    /* 5. 卡片樣式 (扁平化設計) */
    .app-card {{
        background-color: {CARD_COLOR} !important;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        position: relative;
    }}
    
    /* 6. 導遊框 (強制樣式) */
    .guide-box {{
        background-color: #FFF8E1 !important;
        border-left: 5px solid #FFC107;
        padding: 10px;
        margin-top: 10px;
        border-radius: 4px;
        font-size: 0.9rem;
    }}
    
    /* 7. 天氣 Widget */
    .weather-card {{
        background: linear-gradient(135deg, #8E2F2F 0%, #D6A6A6 100%);
        border-radius: 12px;
        padding: 15px;
        color: white !important;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    /* 強制天氣卡內的文字為白色 */
    .weather-card div, .weather-card span {{
        color: white !important;
    }}

    /* 8. 按鈕與標籤 */
    .nav-btn {{
        display: inline-block;
        background-color: white;
        color: #8E2F2F !important;
        border: 1px solid #8E2F2F;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        text-decoration: none;
        margin-left: 5px;
    }}
    
    .ai-tag {{
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.8rem;
        color: white !important;
        margin-right: 4px;
        font-weight: bold;
    }}
    </style>
""", unsafe_allow_html=True)

# -------------------------------------
# 2. 邏輯函數
# -------------------------------------
GUIDE_DB = {
    "Outlet": {"t": "💡 攻略", "c": "臨空城 Outlet 是西日本最大，風格仿美國港口。"},
    "貴志": {"t": "🐱 貓站長", "c": "必看二代玉站長，車站屋頂也是貓耳造型。"},
    "白濱": {"t": "♨️ 溫泉", "c": "日本三大古湯之一，白良濱沙灘非常美。"},
    "租車": {"t": "🚗 提醒", "c": "記得帶台灣駕照 + 日文譯本。"},
    "清水寺": {"t": "⛩️ 歷史", "c": "必看清水舞台，完全沒用釘子建造。"}
}

def get_guide_html(title, loc):
    # 簡單關鍵字搜尋
    key = str(title) + str(loc)
    for k, v in GUIDE_DB.items():
        if k in key:
            # 使用單行字串拼接，避免縮排錯誤
            return f'<div class="guide-box"><b>{v["t"]}：</b>{v["c"]}</div>'
    return ""

def highlight_html(text):
    if not text: return ""
    # 單行 HTML
    text = re.sub(r'(必吃|推薦)', r'<span class="ai-tag" style="background:#FF9800;">🍱 \1</span>', text)
    text = re.sub(r'(必買|伴手禮)', r'<span class="ai-tag" style="background:#F44336;">🛍️ \1</span>', text)
    text = re.sub(r'(預約|代號)', r'<span class="ai-tag" style="background:#2196F3;">🎫 \1</span>', text)
    return text

def nav_link(loc):
    if not loc: return ""
    url = f"https://www.google.com/maps/dir/?api=1&destination={urllib.parse.quote(loc)}&travelmode=driving"
    return f'<a href="{url}" target="_blank" class="nav-btn">🚗 導航</a>'

# -------------------------------------
# 3. 資料初始化
# -------------------------------------
if "trip_data" not in st.session_state:
    st.session_state.trip_data = {
        1: [
            {"id": 1, "time": "10:00", "title": "關西機場 租車", "loc": "關西機場 Aeroplaza", "cost": 15000, "cat": "trans", "note": "預約代號 KIX-8821"},
            {"id": 2, "time": "12:30", "title": "臨空城 Outlet", "loc": "Rinku Premium Outlets", "cost": 3000, "cat": "food", "note": "必吃 KUA`AINA 漢堡"},
            {"id": 3, "time": "15:00", "title": "貴志車站", "loc": "和歌山 貴志駅", "cost": 0, "cat": "spot", "note": "必買 貓咪周邊"},
            {"id": 4, "time": "18:00", "title": "白濱溫泉 住宿", "loc": "白濱萬豪酒店", "cost": 0, "cat": "stay", "note": "Check-in 享受溫泉"}
        ],
        2: [], 3: [], 4: [], 5: []
    }

if "pack_list" not in st.session_state:
    st.session_state.pack_list = {
        "證件": {"護照": False, "駕照譯本": False},
        "電子": {"網卡": False, "充電器": False}
    }

# -------------------------------------
# 4. 主畫面渲染
# -------------------------------------
st.markdown("<h2 style='text-align:center; margin-bottom:10px;'>2026 阪京自駕遊 🇯🇵</h2>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📅 行程", "🗺️ 地圖", "ℹ️ 資訊"])

# --- TAB 1: 行程 ---
with tab1:
    # 天數選擇 (已用 CSS 改為按鈕樣式)
    days = sorted(st.session_state.trip_data.keys())
    day = st.radio(" ", days, format_func=lambda x: f"Day {x}", horizontal=True, label_visibility="collapsed")
    
    # 天氣卡 (單行 HTML)
    w_text = "🌤️ 12°C 晴時多雲" if day == 1 else "🌧️ 10°C 雨天備案"
    st.markdown(f'<div class="weather-card"><div><b>Day {day} 天氣預報</b><br>{w_text}</div><div style="font-size:2rem;">🌤️</div></div>', unsafe_allow_html=True)
    
    # 編輯模式
    col_a, col_b = st.columns([1, 3])
    is_edit = col_a.toggle("編輯")
    if is_edit and col_b.button("➕ 新增"):
        st.session_state.trip_data[day].append({"id": int(time.time()), "time": "12:00", "title": "新行程", "loc": "", "cost": 0, "cat": "spot", "note": ""})
        st.rerun()

    # 顯示列表
    items = sorted(st.session_state.trip_data[day], key=lambda x: x['time'])
    if not items: st.info("尚無行程")
    
    for i, item in enumerate(items):
        # 顏色定義
        c_map = {"trans": "#9E9E9E", "food": "#FF9800", "spot": "#F44336", "stay": "#3F51B5", "shop": "#E91E63"}
        bar_color = c_map.get(item.get('cat', 'spot'), "#9E9E9E")
        
        # HTML 組合 (全部單行，防止代碼外洩)
        title_html = f'<div style="font-size:1.1rem; font-weight:bold;">{item["title"]}</div>'
        meta_html = f'<div style="display:flex; justify-content:space-between; color:#666; font-size:0.9rem;"><span>{item["time"]}</span><span>¥{item["cost"]:,}</span></div>'
        loc_html = f'<div style="font-size:0.85rem; color:#555; margin-top:4px;">📍 {item["loc"] if item["loc"] else "無地點"} {nav_link(item["loc"])}</div>'
        note_html = f'<div style="font-size:0.9rem; margin-top:6px;">{highlight_html(item["note"])}</div>'
        guide_html = "" if is_edit else get_guide_html(item["title"], item["loc"])
        
        # 最終卡片輸出
        st.markdown(
            f'<div class="app-card" style="border-left: 5px solid {bar_color};">'
            f'{meta_html}{title_html}{loc_html}{note_html}{guide_html}'
            f'</div>', 
            unsafe_allow_html=True
        )

        # 編輯區塊
        if is_edit:
            with st.container():
                c1, c2 = st.columns([1, 2])
                item['time'] = c1.text_input(f"時間{item['id']}", item['time'])
                item['title'] = c2.text_input(f"標題{item['id']}", item['title'])
                item['loc'] = st.text_input(f"地點{item['id']}", item['loc'])
                item['note'] = st.text_area(f"筆記{item['id']}", item['note'])
                item['cat'] = st.selectbox(f"分類{item['id']}", ["spot", "food", "stay", "trans"], index=0)
                if st.button("🗑️ 刪除", key=f"del_{item['id']}"):
                    st.session_state.trip_data[day].pop(i)
                    st.rerun()

# --- TAB 2: 地圖 ---
with tab2:
    st.caption("🗺️ Google Maps 路線連結")
    map_day = st.selectbox("選擇日期", days)
    d_items = sorted(st.session_state.trip_data[map_day], key=lambda x: x['time'])
    locs = [x['loc'] for x in d_items if x['loc']]
    
    if len(locs) > 1:
        origin = urllib.parse.quote(locs[0])
        dest = urllib.parse.quote(locs[-1])
        waypoints = "|".join([urllib.parse.quote(x) for x in locs[1:-1]])
        url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={dest}&waypoints={waypoints}&travelmode=driving"
        
        st.markdown(f'''
            <a href="{url}" target="_blank" style="display:block; text-align:center; background:#8E2F2F; color:white; padding:12px; border-radius:8px; text-decoration:none; margin-bottom:15px; font-weight:bold;">
                🚗 開啟導航路線 ({len(locs)}個地點)
            </a>
        ''', unsafe_allow_html=True)
    else:
        st.warning("需至少兩個地點才能計算路線")
        
    for x in d_items:
        st.markdown(f"- **{x['time']}** {x['title']}")

# --- TAB 3: 資訊 ---
with tab3:
    st.markdown("### ℹ️ 旅遊資訊")
    
    with st.expander("✈️ 航班 & 住宿", expanded=True):
        st.markdown("""
        **去程 JX821**: 01/17 10:00 -> 13:30  
        **回程 JX822**: 01/22 15:00 -> 17:30
        
        **🏨 住宿**:
        * D1: 白濱萬豪 (882199)
        * D2: 大阪 Cross (Booking)
        """)
        
    with st.expander("🆘 緊急聯絡"):
        st.error("警察 110 | 救護車 119")
        st.write("駐日代表處: +81-3-3280-7811")
        
    with st.expander("💰 預算概況"):
        total = sum([x['cost'] for d in st.session_state.trip_data.values() for x in d])
        st.metric("總預算 (JPY)", f"¥{total:,}")

    with st.expander("🧳 行李清單"):
        for cat, items in st.session_state.pack_list.items():
            st.markdown(f"**{cat}**")
            cols = st.columns(2)
            for idx, (k, v) in enumerate(items.items()):
                st.session_state.pack_list[cat][k] = cols[idx%2].checkbox(k, v, key=f"p_{k}")