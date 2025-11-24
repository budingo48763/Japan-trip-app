import streamlit as st
import pandas as pd
import graphviz
import matplotlib.pyplot as plt
import requests
from datetime import datetime
from streamlit-sortable import sortable

# 類別樣式與 emoji
category_style = {
    "餐飲": {"color": "lightcoral", "emoji": "🍽️"},
    "交通": {"color": "lightskyblue", "emoji": "🚄"},
    "門票": {"color": "lightgreen", "emoji": "🎫"},
    "購物": {"color": "khaki", "emoji": "🛍️"},
    "住宿": {"color": "plum", "emoji": "🛏️"},
    "其他": {"color": "lightgray", "emoji": "📌"}
}

# 頁面設定與樣式
st.set_page_config(page_title="旅日小幫手 🇯🇵", page_icon="🌸", layout="wide")

st.markdown("""
    <style>
    .big-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ff4b4b;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: gray;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-header">🌸 旅日小幫手</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">你的隨身日本旅遊嚮導</div>', unsafe_allow_html=True)

# -------------------------------
# 出發前準備
# -------------------------------
st.header("🎒 出發前 Check List")

col1, col2 = st.columns(2)
with col1:
    st.subheader("必備文件")
    st.checkbox("護照 (有效期限6個月以上)")
    st.checkbox("Visit Japan Web 填寫完成 (QR Code 截圖)")
    st.checkbox("機票電子檔 / 訂位代號")
    st.checkbox("飯店訂房憑證")
    st.checkbox("海外旅遊保險單")
with col2:
    st.subheader("行李與網路")
    st.checkbox("eSIM / SIM卡 / Wifi機")
    st.checkbox("日幣現金 (不用換太多，刷卡為主)")
    st.checkbox("信用卡 (建議帶兩張以上)")
    st.checkbox("行動電源 + 充電線")
    st.checkbox("個人常備藥品")

st.info("💡 小撇步：把護照影本存在手機雲端備份，以備不時之需。")

# -------------------------------
# 搭機流程圖與當地須知
# -------------------------------
st.header("✈️ 搭機流程 & 當地小知識")

st.subheader("機場通關流程圖")
airport_flow = graphviz.Digraph()
airport_flow.attr(rankdir='LR', size='10')
airport_flow.node('A', '抵達機場\n(起飛前2.5hr)')
airport_flow.node('B', '報到託運\nCheck-in')
airport_flow.node('C', '安全檢查\nSecurity')
airport_flow.node('D', '證照查驗\nImmigration')
airport_flow.node('E', '免稅店/候機')
airport_flow.node('F', '登機\nBoarding')
airport_flow.edges([('A','B'), ('B','C'), ('C','D'), ('D','E'), ('E','F')])
st.graphviz_chart(airport_flow)

st.subheader("🇯🇵 當地小知識")
with st.expander("1. 交通系 IC 卡 (Suica/Pasmo)"):
    st.write("iPhone 用戶可用 Apple Wallet 加入 Suica，用台灣信用卡加值，超方便！")
with st.expander("2. 免稅規定 (Tax Free)"):
    st.write("同一天在同一店家消費滿 5,500 日圓(含稅)即可退稅，現在多為電子化處理。")
with st.expander("3. 垃圾分類"):
    st.write("日本路上很少垃圾桶，建議帶回飯店或找便利商店丟。")

# -------------------------------
# 行程流程圖產生器
# -------------------------------
st.header("🗺️ 行程流程圖產生器")

day_input = st.text_area("輸入行程（用箭頭 '->' 或逗號 ',' 分隔景點）", 
                         value="東京車站 -> 明治神宮 -> 竹下通逛街 -> 澀谷 Sky 看夜景 -> 居酒屋晚餐",
                         height=100)

if st.button("🎨 產生行程圖"):
    items = [x.strip() for x in day_input.replace("->", ",").split(",") if x.strip()]
    if items:
        trip_flow = graphviz.Digraph()
        trip_flow.attr(rankdir='TB')
        trip_flow.attr('node', shape='box', style='filled', color='lightblue', fontname="Microsoft JhengHei")
        for i in range(len(items)):
            trip_flow.node(str(i), items[i])
            if i > 0:
                trip_flow.edge(str(i-1), str(i))
        st.graphviz_chart(trip_flow)
    else:
        st.warning("請輸入至少一個景點喔！")

# -------------------------------
# 快速記帳功能
# -------------------------------
st.header("💰 快速記帳")

if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["項目", "金額 (JPY)", "類別", "時間"])

col_input1, col_input2, col_input3 = st.columns([2, 1, 1])
with col_input1:
    item_name = st.text_input("消費項目", placeholder="例如：一蘭拉麵")
with col_input2:
    item_price = st.number_input("金額 (日幣)", min_value=0, step=100)
with col_input3:
    item_cat = st.selectbox("類別", ["餐飲", "交通", "購物", "住宿", "門票"])

if st.button("➕ 新增一筆"):
    if item_name and item_price > 0:
        new_data = pd.DataFrame({
            "項目": [item_name],
            "金額 (JPY)": [item_price],
            "類別": [item_cat],
            "時間": [datetime.now().strftime("%H:%M")]
        })
        st.session_state.expenses = pd.concat([st.session_state.expenses, new_data], ignore_index=True)
        st.success("已記帳！")
    else:
        st.error("請輸入項目名稱與金額")

if not st.session_state.expenses.empty:
    total_expense = st.session_state.expenses["金額 (JPY)"].sum()
    st.markdown(f"### 目前總花費: <span style='color:red'>¥{total_expense:,}</span>", unsafe_allow_html=True)
    st.dataframe(st.session_state.expenses, use_container_width=True)
    st.subheader("消費比例分析")
    chart_data = st.session_state.expenses.groupby("類別")["金額 (JPY)"].sum()
    st.bar_chart(chart_data)
    if st.button("🗑️ 清除所有記帳"):
        st.session_state.expenses = pd.DataFrame(columns=["項目", "金額 (JPY)", "類別", "時間"])
        st.experimental_rerun()
else:
    st.info("目前還沒有消費紀錄，快去買買買吧！")

# -------------------------------
# 多日行程 + 拖拉排序 + 分析
# -------------------------------
st.header("📅 多日行程規劃")

if "trip_data" not in st.session_state:
    st.session_state.trip_data = {f"Day {i}": [] for i in range(1, 8)}

selected_day = st.selectbox("選擇行程日", list(st.session_state.trip_data.keys()))

if not st.session_state.trip_data[selected_day]:
    st.session_state.trip_data[selected_day] = [
        {"時間": "07:00", "地點": "相鐵FRESA INN", "備註": "起床 & 早餐", "金額": 0, "類別": "餐飲", "地圖": "https://maps.google.com/?q=相鐵FRESA INN"},
        {"時間": "08:00", "地點": "名古屋 → 上諏訪", "備註": "JR 特急（信濃號）", "金額": 0, "類別": "交通", "地圖": "https://maps.google.com/?q=名古屋站"},
        {"時間": "10:30", "地點": "高島城跡", "備註": "城堡遺跡，營業至16:30", "金額": 500, "類別": "門票", "地圖": "https://maps.google.com/?q=高島城跡"}
    ]

sorted_items = sortable(items=st.session_state.trip_data[selected_day], item_key="地點", direction="vertical")

for i, item in enumerate(sorted_items):
    with st.expander(f"📝 編輯：{item['時間']} {item['地點']}"):
        item["時間"] = st.text_input("時間", value=item["時間"], key=f"time_{selected_day}_{i}")
        item["地點"] = st.text_input("地點", value=item["地點"], key=f"place_{selected_day}_{i}")
        item["備註"] = st.text_area("備註", value=item["備註"], key=f"note_{selected_day}_{i}")
        item["金額"] = st.number_input("金額 (JPY)", value=item["金額"], key=f"price_{selected_day}_{i}")
        item["類別"] = st.selectbox("類別", list(category_style.keys()), index=list(category_style.keys()).index(item["類別"]), key=f"cat_{selected_day}_{i}")
        item["地圖"] = st.text_input("地圖連結", value=item["地圖"], key=f"map_{selected_day}_{i}")

st.session_state.trip_data[selected_day] = sorted_items

st.divider()
st.markdown("### 🎨 行程流程圖 + 記帳分析")

# 行程流程圖
flow = graphviz.Digraph()
flow.attr(rankdir='TB')
for i, item in enumerate(sorted_items):
    style = category_style.get(item["類別"], category_style["其他"])
    label = f"{style['emoji']} {item['時間']}\\n{item['地點']}\\n{item['備註']}\\n¥{item['金額']}"
    flow.node(str(i), label, style='filled', color=style["color"], fontname="Microsoft JhengHei")
    if i > 0:
        flow.edge(str(i-1), str(i))
st.graphviz_chart(flow)

# 記帳明細表格
df = pd.DataFrame(sorted_items)
st.subheader("📋 記帳明細")
st.dataframe(df, use_container_width=True)

# 類別統計長條圖
st.subheader("📊 類別消費比例")
chart_data = df.groupby("類別")["金額"].sum()
st.bar_chart(chart_data)

# 圓餅圖分析
fig, ax = plt.subplots()
ax.pie(chart_data, labels=chart_data.index, autopct='%
