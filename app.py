# 檔名: app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# 設定頁面
st.set_page_config(page_title="NBA 球員能力查詢", layout="wide")
st.title("NBA 球員能力查詢")

# 讀取剛剛處理好的資料 (需確保 clean_nba_data.csv 存在)
@st.cache_data
def load_data():
    return pd.read_csv("clean_nba_data.csv")

clean_data = load_data()

# 建立側邊欄 (Sidebar)
st.sidebar.header("篩選條件")

team_options = ["全部球隊"] + list(clean_data['Team'].unique())
selected_team = st.sidebar.selectbox("選擇隊伍:", team_options)

ability_options = ["SPV", "PTS_VAL", "REB_VAL", "AST_VAL", "STL_VAL", "BLK_VAL", "TOV_VAL"]
selected_ability = st.sidebar.selectbox("選擇能力:", ability_options)

# 篩選資料
if selected_team == "全部球隊":
    filtered_data = clean_data
else:
    filtered_data = clean_data[clean_data['Team'] == selected_team]

# 主畫面切割為兩欄 (如果你想要並排，也可以上下放)
st.subheader(f"目前顯示: {selected_team} 的 {selected_ability} 能力值")

# 1. 顯示資料表 (對應 DT::dataTableOutput)
display_cols = ["Player", "Team", "cluster", selected_ability, "Salary"]
st.dataframe(filtered_data[display_cols], use_container_width=True)

# 2. 顯示散佈圖 (對應 plotOutput)
# 使用 Plotly Express 製作互動式圖表，滑鼠游標移過去會顯示球員名字 (比 ggplot 更方便！)
fig = px.scatter(
    filtered_data, 
    x=selected_ability, 
    y="Salary", 
    color=filtered_data['cluster'].astype(str), # 將分群轉為字串以作為離散顏色
    hover_name="Player", # 滑鼠停留在點上會顯示 Player 名字
    labels={"cluster": "分群", "Salary": "薪水", selected_ability: f"{selected_ability} 能力值"},
    title=f"{selected_team} 能力: {selected_ability} 與薪資的關係",
    size_max=10
)
fig.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
st.plotly_chart(fig, use_container_width=True)