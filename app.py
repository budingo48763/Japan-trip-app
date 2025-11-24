import streamlit as st
import pandas as pd
import graphviz
import matplotlib.pyplot as plt
import platform
import urllib.parse
import random
from datetime import datetime, timedelta

# -------------------------------------
# 1. 系統設定
# -------------------------------------
st.set_page_config(page_title="旅日小幫手 Pro 🇯🇵", page_icon="🌸", layout="centered")

# 字體設定 (維持不變)
system_platform = platform.system()
if system_platform == "Windows":
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
else:
    plt.rcParams['font.family'] = ['sans-serif']
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'Noto Sans CJK JP', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# -------------------------------------
# 2. 自定義 CSS
# -------------------------------------
st.markdown("""
    <style>
    .stApp { font-family: 'Helvetica Neue', Helvetica, 'Microsoft JhengHei', Arial, sans-serif; }
    .big-header { font-size: 1.8rem; font-weight: 800; color: #E63946; margin: 0; }
    .sub-header { font-size: 0.9rem; color: gray; margin-bottom: 10px; }
    
    /* 卡片樣式 */
    .trip-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 6px solid #ccc;
        transition: transform 0.2s;
    }
    .trip-card:hover { transform: translateY(-2px); }
    
    /* 時間軸樣式 */
    .time-label { font-size: 1.1rem; font-weight: 700; color: #333; }
    .date-badge { 
        background-color: #E63946; color: white; 
        padding: 4px 10px; border-radius: 20px; 
        font-size: 0.8rem; font-weight: bold; margin-bottom: 10px; display: inline-block;
    }
    
    /* 天氣小卡 */
    .weather-widget {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 10px; border-radius: 10px; color: #555; text-align: center;
        font-size: 0.9rem; font-weight: bold;
    }

    /* 類別顏色 */
    .cat-food { border-left-color: #FF6B6B !important; }
    .cat-transport { border-left-color: #4ECDC4 !important; }
    .cat-ticket { border-left-color: #FFE66D !important; }
    .cat-shop { border-left-color: #1A535C !important; }
    .cat-hotel { border-left-color: #5E548E !important; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------
# 3. 初始化資料與邏輯
# -------------------------------------

# 初始化行程資料結構
if "trip_data" not in st.session_state:
    st.session_state.trip_data = {
        1: [ # 使用數字 key 代表第幾天
            {"id": 1, "time": "08:00", "title": "前往機場", "location": "桃園機場 T1", "cost": 0, "cat": "交通", "note": "記得帶護照"},
            {"id": 2, "time": "15:30", "title": "Check-in", "location": "名古屋飯店", "cost": 15000, "cat": "住宿", "note": "寄放行李"},
        ],
        2: [
            {"id": 3, "time": "11:30", "title": "午餐：鰻魚飯", "location": "蓬萊軒", "cost": 4500, "cat": "餐飲", "note": "排隊名店"},
        ]
    }

category_map = {
    "餐飲": {"color": "cat-food", "emoji": "🍽️"},
    "交通": {"color": "cat-transport", "emoji": "🚄"},
    "門票": {"color": "cat-ticket", "emoji": "🎫"},
    "購物": {"color": "cat-shop", "emoji": "🛍️"},
    "住宿": {"color": "cat-hotel", "emoji": "🛏️"},
    "其他": {"color": "", "emoji": "📌"}
}

def get_map_link(query):
    if not query: return "#"
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(query)

# 模擬天氣函數 (因為原程式碼沒有，這裡做一個模擬效果)
def get_mock_weather():
    weathers = [("☀️ 晴朗", "18°C"), ("☁️ 多雲", "16°C"), ("🌧️ 小雨", "14°C"), ("🌤️ 晴時多雲", "17°C")]
    return random.choice(weathers)

# -------------------------------------
# 4. 側邊欄設定 (日期與天數)
# -------------------------------------
with st.sidebar:
    st.header("⚙️ 行程設定")
    start_date = st.date_input("出發日期", value=datetime.today())
    trip_days = st.number_input("旅遊天數", min_value=1, max_value=30, value=5)
    
    st.divider()
    
    # 編輯模式開關
    is_edit_mode = st.toggle("✏️ 啟用編輯模式", value=False)
    if is_edit_mode:
        st.info("現在可以新增、修改或刪除行程")
    else:
        st.caption("目前為瀏覽模式")

    st.divider()
    st.markdown("Made with ❤️ by Streamlit")

# -------------------------------------
# 5. 主畫面
# -------------------------------------
st.markdown('<div class="big-header">🌸 旅日小幫手 Pro</div>', unsafe_allow_html=True)

# 動態計算日期文字 (例如: 2023-11-24 Fri)
end_date = start_date + timedelta(days=trip_days - 1)
date_range_str = f"{start_date.strftime('%Y/%m/%d')} - {end_date.strftime('%m/%d')}"
st.markdown(f'<div class="sub-header">{date_range_str} • 共 {trip_days} 天</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📅 行程總覽", "📊 預算統計", "🎒 準備清單"])

# ==========================================
# TAB 1: 行程規劃 (核心功能)
# ==========================================
with tab1:
    # 產生日期選項
    day_options = {}
    for i in range(trip_days):
        current_date = start_date + timedelta(days=i)
        day_num = i + 1
        day_str = f"Day {day_num} ({current_date.strftime('%m/%d %a')})"
        day_options[day_str] = day_num
        
        # 確保資料結構中有這一天
        if day_num not in st.session_state.trip_data:
            st.session_state.trip_data[day_num] = []

    # 選擇天數
    selected_day_label = st.selectbox("選擇日期", list(day_options.keys()), label_visibility="collapsed")
    selected_day_idx = day_options[selected_day_label]
    
    # 取得當日資料
    current_items = st.session_state.trip_data[selected_day_idx]

    # --- 頂部資訊列 (天氣 + 花費) ---
    col_info1, col_info2 = st.columns([3, 1])
    with col_info1:
        daily_cost = sum(item['cost'] for item in current_items)
        st.markdown(f"#### 📅 {selected_day_label}")
        st.caption(f"當日預算: ¥{daily_cost:,}")
    with col_info2:
        # 顯示天氣 (模擬)
        w_icon, w_temp = get_mock_weather()
        st.markdown(f"""
        <div class="weather-widget">
            <div>{w_icon}</div>
            <div>{w_temp}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 新增行程 (只在編輯模式顯示) ---
    if is_edit_mode:
        with st.expander("➕ 新增一筆行程", expanded=False):
            c1, c2 = st.columns([1, 2])
            new_time = c1.time_input("時間", value=datetime.strptime("09:00", "%H:%M").time())
            new_title = c2.text_input("行程標題", placeholder="例如：清水寺")
            c3, c4 = st.columns([2, 1])
            new_loc = c3.text_input("地點", placeholder="用於地圖搜尋")
            new_cat = c4.selectbox("類別", list(category_map.keys()))
            new_cost = st.number_input("金額 (JPY)", step=1000)
            new_note = st.text_area("備註")
            
            if st.button("確認新增", type="primary"):
                new_item = {
                    "id": int(datetime.now().timestamp()),
                    "time": new_time.strftime("%H:%M"),
                    "title": new_title or "未命名",
                    "location": new_loc,
                    "cost": new_cost,
                    "cat": new_cat,
                    "note": new_note
                }
                st.session_state.trip_data[selected_day_idx].append(new_item)
                st.session_state.trip_data[selected_day_idx].sort(key=lambda x: x['time'])
                st.rerun()
        st.markdown("---")

    # --- 行程列表顯示 ---
    if not current_items:
        st.info("💤 這一天目前沒有安排行程")
    
    for i, item in enumerate(current_items):
        style = category_map.get(item["cat"], category_map["其他"])
        
        col_time, col_card = st.columns([1, 4])
        
        # 左側時間
        with col_time:
            st.markdown(f"<div style='text-align:right; padding-top:15px;'><span class='time-label'>{item['time']}</span></div>", unsafe_allow_html=True)
        
        # 右側卡片
        with col_card:
            card_html = f"""
            <div class="trip-card {style['color']}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:1.1rem;"><strong>{style['emoji']} {item['title']}</strong></div>
                    <div style="background:#eee; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:0.8rem;">¥{item['cost']:,}</div>
                </div>
                <div style="color:#666; font-size:0.9rem; margin-top:4px;">📍 {item['location'] if item['location'] else '無地點資訊'}</div>
                <div style="color:#888; font-size:0.85rem; margin-top:4px; font-style:italic;">{item['note']}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            # --- 按鈕區 (地圖 / 編輯 / 刪除) ---
            # 只有在有地點時顯示地圖，只有在編輯模式時顯示編輯刪除
            cols = st.columns([1, 1, 1, 3])
            
            # 1. 地圖按鈕 (永遠顯示)
            with cols[0]:
                 if item['location']:
                    st.link_button("🗺️", get_map_link(item['location']), help="Google Maps")
            
            # 2. 編輯與刪除 (受開關控制)
            if is_edit_mode:
                with cols[1]:
                    # 使用 Popover 進行原地編輯
                    with st.popover("✏️", help="編輯內容"):
                        e_title = st.text_input("標題", item["title"], key=f"t_{selected_day_idx}_{item['id']}")
                        e_time = st.text_input("時間", item["time"], key=f"tm_{selected_day_idx}_{item['id']}")
                        e_cost = st.number_input("金額", value=item["cost"], key=f"c_{selected_day_idx}_{item['id']}")
                        e_note = st.text_area("備註", item["note"], key=f"n_{selected_day_idx}_{item['id']}")
                        if st.button("保存", key=f"save_{selected_day_idx}_{item['id']}"):
                            item["title"] = e_title
                            item["time"] = e_time
                            item["cost"] = e_cost
                            item["note"] = e_note
                            st.session_state.trip_data[selected_day_idx].sort(key=lambda x: x['time'])
                            st.rerun()
                with cols[2]:
                    if st.button("🗑️", key=f"del_{selected_day_idx}_{item['id']}", help="刪除"):
                        st.session_state.trip_data[selected_day_idx].pop(i)
                        st.rerun()

# ==========================================
# TAB 2: 預算分析
# ==========================================
with tab2:
    all_expenses = []
    for day_num, items in st.session_state.trip_data.items():
        if day_num > trip_days: continue # 超過設定天數的不計算
        for item in items:
            if item['cost'] > 0:
                all_expenses.append({"Day": f"Day {day_num}", "Item": item['title'], "Category": item['cat'], "Cost": item['cost']})
    
    if all_expenses:
        df = pd.DataFrame(all_expenses)
        st.metric("💰 總旅費預估", f"¥{df['Cost'].sum():,}")
        st.bar_chart(df.groupby("Category")["Cost"].sum())
        st.dataframe(df, use_container_width=True)
    else:
        st.info("尚未輸入任何消費金額")

# ==========================================
# TAB 3: 準備清單
# ==========================================
with tab3:
    st.checkbox("護照 / 簽證")
    st.checkbox("Visit Japan Web")
    st.checkbox("網卡 / eSIM")
    st.checkbox("日幣現金")