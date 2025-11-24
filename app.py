import streamlit as st
import pandas as pd
import graphviz
import matplotlib.pyplot as plt
import platform
import urllib.parse
from datetime import datetime

# -------------------------------------
# 1. 系統設定與中文字體修正
# -------------------------------------
st.set_page_config(page_title="旅日小幫手 🇯🇵", page_icon="🌸", layout="centered")

system_platform = platform.system()
if system_platform == "Windows":
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
else:
    plt.rcParams['font.family'] = ['sans-serif']
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'Noto Sans CJK JP', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# -------------------------------------
# 2. 自定義 CSS (讓介面像 App)
# -------------------------------------
st.markdown("""
    <style>
    /* 全域字體優化 */
    .stApp { font-family: 'Helvetica Neue', Helvetica, 'Microsoft JhengHei', Arial, sans-serif; }
    
    /* 標題樣式 */
    .big-header { font-size: 2rem; font-weight: 800; color: #E63946; margin-bottom: 0px; text-align: center; }
    .sub-header { font-size: 1rem; color: gray; margin-bottom: 20px; text-align: center; }
    
    /* 行程卡片樣式 */
    .trip-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid #FF9F1C; /* 預設橘色 */
    }
    
    /* 時間軸樣式 */
    .time-label { font-size: 1.2rem; font-weight: bold; color: #333; }
    .location-link a { text-decoration: none; color: #457B9D; font-size: 0.9rem; }
    .cost-tag { background-color: #F1FAEE; color: #1D3557; padding: 2px 8px; border-radius: 5px; font-size: 0.8rem; font-weight: bold; float: right; }
    
    /* 類別顏色定義 */
    .cat-food { border-left-color: #E63946 !important; }   /* 紅色-餐飲 */
    .cat-transport { border-left-color: #457B9D !important; } /* 藍色-交通 */
    .cat-ticket { border-left-color: #2A9D8F !important; }    /* 綠色-門票 */
    .cat-shop { border-left-color: #F4A261 !important; }      /* 橘色-購物 */
    .cat-hotel { border-left-color: #9B5DE5 !important; }     /* 紫色-住宿 */
    </style>
""", unsafe_allow_html=True)

# -------------------------------------
# 3. 初始化 Session State (資料結構)
# -------------------------------------
if "trip_data" not in st.session_state:
    # 預設範例資料 (模仿截圖)
    st.session_state.trip_data = {
        "Day 1": [
            {"id": 1, "time": "08:00", "title": "前往機場", "location": "桃園機場 T1", "cost": 0, "cat": "交通", "note": "記得帶護照"},
            {"id": 2, "time": "11:35", "title": "飛往名古屋", "location": "名古屋中部國際機場", "cost": 0, "cat": "交通", "note": "CX530"},
            {"id": 3, "time": "15:30", "title": "Check-in", "location": "相鐵FRESA INN", "cost": 15000, "cat": "住宿", "note": "寄放行李"},
            {"id": 4, "time": "18:00", "title": "晚餐：矢場味噌豬排", "location": "矢場町本店", "cost": 2000, "cat": "餐飲", "note": "必點鐵板豬排"},
        ],
        "Day 2": [
            {"id": 5, "time": "08:00", "title": "移動：名古屋 -> 上諏訪", "location": "JR 名古屋站", "cost": 3000, "cat": "交通", "note": "搭乘信濃號"},
            {"id": 6, "time": "11:30", "title": "午餐：鰻魚飯", "location": "古色古香名店", "cost": 2000, "cat": "餐飲", "note": ""},
            {"id": 7, "time": "13:30", "title": "高島城跡", "location": "高島城", "cost": 300, "cat": "門票", "note": "拍照景點"},
        ],
        "Day 3": [], "Day 4": [], "Day 5": []
    }

category_map = {
    "餐飲": {"color": "cat-food", "emoji": "🍽️"},
    "交通": {"color": "cat-transport", "emoji": "🚄"},
    "門票": {"color": "cat-ticket", "emoji": "🎫"},
    "購物": {"color": "cat-shop", "emoji": "🛍️"},
    "住宿": {"color": "cat-hotel", "emoji": "🛏️"},
    "其他": {"color": "", "emoji": "📌"}
}

# -------------------------------------
# 4. Helper Function: Google Map Link
# -------------------------------------
def get_map_link(query):
    if not query: return "#"
    base = "https://www.google.com/maps/search/?api=1&query="
    return base + urllib.parse.quote(query)

# -------------------------------------
# 5. 主畫面 UI
# -------------------------------------

# 頂部標題
st.markdown('<div class="big-header">🌸 旅日小幫手</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{datetime.now().strftime("%Y-%m-%d")} • 日本旅行規劃</div>', unsafe_allow_html=True)

# 建立分頁
tab1, tab2, tab3 = st.tabs(["📅 行程規劃", "📊 預算分析", "🎒 行前準備"])

# ==========================================
# TAB 1: 行程規劃 (核心功能)
# ==========================================
with tab1:
    # --- 天數選擇 ---
    days = list(st.session_state.trip_data.keys())
    selected_day = st.selectbox("選擇日期", days, label_visibility="collapsed")
    
    current_items = st.session_state.trip_data[selected_day]
    
    # 計算當日花費
    daily_cost = sum(item['cost'] for item in current_items)
    st.info(f"💰 {selected_day} 預估花費: ¥{daily_cost:,}")

    # --- 新增行程區塊 ---
    with st.expander("➕ 新增行程", expanded=False):
        c1, c2 = st.columns([1, 2])
        new_time = c1.time_input("時間", value=datetime.strptime("09:00", "%H:%M").time())
        new_title = c2.text_input("行程標題", placeholder="例如：晴空塔")
        c3, c4 = st.columns([2, 1])
        new_loc = c3.text_input("地點 (用於地圖)", placeholder="輸入地點名稱")
        new_cat = c4.selectbox("類別", list(category_map.keys()))
        new_cost = st.number_input("預估金額 (JPY)", step=100, min_value=0)
        new_note = st.text_area("備註")
        
        if st.button("加入行程", type="primary"):
            new_item = {
                "id": int(datetime.now().timestamp()), # 簡單的 ID
                "time": new_time.strftime("%H:%M"),
                "title": new_title if new_title else "未命名行程",
                "location": new_loc,
                "cost": new_cost,
                "cat": new_cat,
                "note": new_note
            }
            # 插入並排序
            st.session_state.trip_data[selected_day].append(new_item)
            st.session_state.trip_data[selected_day].sort(key=lambda x: x['time'])
            st.rerun()

    st.markdown("---")

    # --- 行程列表顯示 (Timeline Style) ---
    if not current_items:
        st.markdown(f"<div style='text-align:center; color:gray; padding:20px;'>{selected_day} 還沒有行程喔！點擊上方新增。</div>", unsafe_allow_html=True)
    
    for i, item in enumerate(current_items):
        # 取得樣式設定
        style = category_map.get(item["cat"], category_map["其他"])
        css_class = style["color"]
        emoji = style["emoji"]
        map_url = get_map_link(item["location"])
        
        # 使用 Streamlit Columns 模擬 App 佈局
        col_time, col_card = st.columns([1.2, 4])
        
        with col_time:
            st.markdown(f"<div style='margin-top:10px; text-align:right;'><span class='time-label'>{item['time']}</span></div>", unsafe_allow_html=True)
            # 顯示連線軸 (視覺裝飾)
            st.markdown("<div style='border-right: 2px solid #ddd; height: 100%; margin-right: 10px;'></div>", unsafe_allow_html=True)

        with col_card:
            # 使用 HTML 渲染卡片外觀
            card_html = f"""
            <div class="trip-card {css_class}">
                <div style="display:flex; justify-content:space-between;">
                    <strong>{emoji} {item['title']}</strong>
                    <span class="cost-tag">¥{item['cost']:,}</span>
                </div>
                <div style="color:gray; font-size:0.9rem; margin-top:5px;">📍 {item['location'] if item['location'] else '無地點'}</div>
                <div style="font-size:0.85rem; color:#666; margin-top:5px;">{item['note']}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # 功能按鈕區 (地圖、編輯、刪除)
            bc1, bc2, bc3 = st.columns([1, 1, 1])
            with bc1:
                if item["location"]:
                    st.link_button("🗺️ 地圖", map_url, use_container_width=True)
            with bc2:
                # 這裡使用 Expander 做原地編輯
                with st.popover("✏️ 編輯", use_container_width=True):
                    e_title = st.text_input("標題", item["title"], key=f"t_{selected_day}_{item['id']}")
                    e_time = st.text_input("時間", item["time"], key=f"tm_{selected_day}_{item['id']}")
                    e_cost = st.number_input("金額", value=item["cost"], key=f"c_{selected_day}_{item['id']}")
                    e_note = st.text_area("備註", item["note"], key=f"n_{selected_day}_{item['id']}")
                    if st.button("保存", key=f"save_{selected_day}_{item['id']}"):
                        item["title"] = e_title
                        item["time"] = e_time
                        item["cost"] = e_cost
                        item["note"] = e_note
                        # 重新排序
                        st.session_state.trip_data[selected_day].sort(key=lambda x: x['time'])
                        st.rerun()
            with bc3:
                if st.button("🗑️", key=f"del_{selected_day}_{item['id']}", use_container_width=True):
                    st.session_state.trip_data[selected_day].pop(i)
                    st.rerun()

# ==========================================
# TAB 2: 預算分析
# ==========================================
with tab2:
    st.header("💰 旅費分析")
    
    # 彙整所有資料
    all_expenses = []
    for day, items in st.session_state.trip_data.items():
        for item in items:
            if item['cost'] > 0:
                all_expenses.append({
                    "Day": day,
                    "Item": item['title'],
                    "Category": item['cat'],
                    "Cost": item['cost']
                })
    
    if all_expenses:
        df = pd.DataFrame(all_expenses)
        total_trip_cost = df["Cost"].sum()
        
        st.metric("預估總旅費", f"¥{total_trip_cost:,}")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("按類別花費")
            category_sum = df.groupby("Category")["Cost"].sum()
            st.bar_chart(category_sum)
            
        with col_chart2:
            st.subheader("每日預算趨勢")
            day_sum = df.groupby("Day")["Cost"].sum()
            st.line_chart(day_sum)
            
        st.subheader("消費明細表")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("目前沒有任何消費紀錄，請在行程中輸入金額。")

# ==========================================
# TAB 3: 行前準備 & 機場流程
# ==========================================
with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎒 必備文件")
        st.checkbox("護照 (有效期限6個月以上)")
        st.checkbox("Visit Japan Web (QR Code)")
        st.checkbox("機票 / 飯店憑證")
        st.checkbox("網卡 / Wi-Fi 機")
        st.checkbox("日幣現金 / 信用卡")
    
    with col2:
        st.subheader("💊 生活用品")
        st.checkbox("個人常備藥")
        st.checkbox("行動電源 / 轉接頭")
        st.checkbox("舒適好走的鞋子")
    
    st.divider()
    st.subheader("✈️ 機場通關流程")
    
    # 簡單的 Graphviz 流程圖
    airport_flow = graphviz.Digraph()
    airport_flow.attr(rankdir='LR', size='8,3')
    airport_flow.node('A', '報到\nCheck-in', shape='box', style='filled', fillcolor='lightblue')
    airport_flow.node('B', '安檢\nSecurity', shape='box')
    airport_flow.node('C', '證照查驗\nImmigration', shape='box')
    airport_flow.node('D', '登機\nBoarding', shape='box', style='filled', fillcolor='lightgreen')
    airport_flow.edges([('A','B'), ('B','C'), ('C','D')])
    st.graphviz_chart(airport_flow)