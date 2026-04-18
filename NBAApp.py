
import streamlit as st
import pandas as pd
import plotly.express as px

# 設定頁面
st.set_page_config(page_title="NBA 球員能力查詢", layout="wide")
st.title("NBA 球員能力查詢")

# 讀取剛剛處理好的資料 (確保 clean_nba_data.csv 存在同一個資料夾)
@st.cache_data
def load_data():
    return pd.read_csv("clean_nba_data.csv")

try:
    clean_data = load_data()
except FileNotFoundError:
    st.error("找不到 `clean_nba_data.csv` 檔案！請確認你已經先跑過資料清理的程式碼，並將生成的 csv 檔放在與此程式相同的資料夾中。")
    st.stop()

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

# 主畫面
st.subheader(f"目前顯示: {selected_team} 的 {selected_ability} 能力值")

# 1. 顯示資料表
display_cols = ["Player", "Team", "cluster", selected_ability, "Salary"]
st.dataframe(filtered_data[display_cols], width="stretch")

# 2. 顯示散佈圖
fig = px.scatter(
    filtered_data, 
    x=selected_ability, 
    y="Salary", 
    color=filtered_data['cluster'].astype(str),
    hover_name="Player", 
    labels={"color": "分群", "Salary": "薪水", selected_ability: f"{selected_ability} 能力值"},
    title=f"{selected_team} 能力: {selected_ability} 與薪資的關係",
    size_max=10
)
fig.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
st.plotly_chart(fig, width="stretch")