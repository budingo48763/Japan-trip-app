import streamlit as st
import pandas as pd
import graphviz
from datetime import datetime

# --- 設定頁面 Vibe ---
st.set_page_config(
    page_title="旅日小幫手 🇯🇵",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State 初始化 (用於儲存記帳資料) ---
if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["項目", "金額 (JPY)", "類別", "時間"])

# --- 自訂樣式 ---
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b;
        color: white;
    }
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

# --- 標題 ---
st.markdown('<div class="big-header">🌸 旅日小幫手</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">你的隨身日本旅遊嚮導</div>', unsafe_allow_html=True)

# --- 主選單 (Tabs) ---
tab1, tab2, tab3, tab4 = st.tabs(["🎒 出發前準備", "✈️ 搭機須知", "🗺️ 行程流程圖", "💰 旅費記帳"])

# ==========================================
# Tab 1: 出發前準備
# ==========================================
with tab1:
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

# ==========================================
# Tab 2: 搭飛機須知 & 當地須知
# ==========================================
with tab2:
    st.header("✈️ 搭飛機流程 & 須知")
    
    # 使用 Graphviz 畫出機場流程
    st.subheader("機場通關流程圖")
    airport_flow = graphviz.Digraph()
    airport_flow.attr(rankdir='LR', size='10')
    
    airport_flow.node('A', '抵達機場\n(起飛前2.5hr)')
    airport_flow.node('B', '報到託運\nCheck-in')
    airport_flow.node('C', '安全檢查\nSecurity')
    airport_flow.node('D', '證照查驗\nImmigration')
    airport_flow.node('E', '免稅店/候機')
    airport_flow.node('F', '登機\nBoarding')
    
    airport_flow.edge('A', 'B')
    airport_flow.edge('B', 'C')
    airport_flow.edge('C', 'D')
    airport_flow.edge('D', 'E')
    airport_flow.edge('E', 'F')
    
    st.graphviz_chart(airport_flow)

    st.divider()
    
    st.subheader("🇯🇵 當地小知識")
    with st.expander("1. 交通系 IC 卡 (Suica/Pasmo)"):
        st.write("如果是 iPhone 用戶，可以直接在 Apple Wallet 加入 Suica，用台灣信用卡加值，超級方便！搭電車、超商付款都靠手機。")
    with st.expander("2. 免稅規定 (Tax Free)"):
        st.write("同一天在同一店家消費滿 5,500 日圓(含稅)即可退稅。現在大多是掃描護照電子化處理，不用貼單子了。")
    with st.expander("3. 垃圾分類"):
        st.write("日本路上很少垃圾桶。垃圾建議帶回飯店丟，或是找車站、便利商店的垃圾桶丟。")

# ==========================================
# Tab 3: 行程流程圖產生器
# ==========================================
with tab3:
    st.header("🗺️ 視覺化你的行程")
    st.write("輸入你的行程點，幫你自動畫成漂亮的流程圖！")

    # 簡單的輸入介面
    day_input = st.text_area("輸入行程 (用箭頭 '->' 或 逗號 ',' 分隔景點):", 
                             value="東京車站 -> 明治神宮 -> 竹下通逛街 -> 澀谷 Sky 看夜景 -> 居酒屋晚餐",
                             height=100)
    
    if st.button("🎨 產生行程圖"):
        # 處理字串
        items = [x.strip() for x in day_input.replace("->", ",").split(",") if x.strip()]
        
        if items:
            trip_flow = graphviz.Digraph()
            trip_flow.attr(rankdir='TB') # Top to Bottom
            trip_flow.attr('node', shape='box', style='filled', color='lightblue', fontname="Microsoft JhengHei")
            
            # 建立節點與連結
            for i in range(len(items)):
                trip_flow.node(str(i), items[i])
                if i > 0:
                    trip_flow.edge(str(i-1), str(i))
            
            st.graphviz_chart(trip_flow)
        else:
            st.warning("請輸入至少一個景點喔！")

# ==========================================
# Tab 4: 旅費記帳功能
# ==========================================
with tab4:
    st.header("💰 快速記帳")
    
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

    st.divider()
    
    # 顯示統計
    if not st.session_state.expenses.empty:
        total_expense = st.session_state.expenses["金額 (JPY)"].sum()
        st.markdown(f"### 目前總花費: <span style='color:red'>¥{total_expense:,}</span>", unsafe_allow_html=True)
        
        # 顯示表格
        st.dataframe(st.session_state.expenses, use_container_width=True)
        
        # 簡單圖表
        st.subheader("消費比例分析")
        chart_data = st.session_state.expenses.groupby("類別")["金額 (JPY)"].sum()
        st.bar_chart(chart_data)
        
        # 清除按鈕
        if st.button("🗑️ 清除所有記帳"):
            st.session_state.expenses = pd.DataFrame(columns=["項目", "金額 (JPY)", "類別", "時間"])
            st.experimental_rerun()
    else:
        st.info("目前還沒有消費紀錄，快去買買買吧！")

