import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns

# 設定中文字體以防圖表顯示亂碼 (Windows 預設為微軟正黑體，Mac 可改為 'PingFang HK')
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

# 1. 讀取資料
file_path = "巨量資料分析 NBA 資料.xlsx"
salary_data = pd.read_excel(file_path, sheet_name="Player Salaries")
stats_data = pd.read_excel(file_path, sheet_name="Player Stats Per Game")
adv_data = pd.read_excel(file_path, sheet_name="Player Advanced Stats")

# 重新命名欄位
salary_data.rename(columns={
    "-additional": "PlayerID",
    salary_data.columns[1]: "Player",
    salary_data.columns[2]: "Team",
    salary_data.columns[3]: "Salary"
}, inplace=True)
salary_data = salary_data[["PlayerID", "Player", "Team", "Salary"]]

stats_data.rename(columns={"Player-additional": "PlayerID"}, inplace=True)
adv_data.rename(columns={"Player-additional": "PlayerID"}, inplace=True)

# 清理薪資資料
salary_data['Salary'] = salary_data['Salary'].astype(str).str.replace(r'[$,]', '', regex=True)
salary_data['Salary'] = pd.to_numeric(salary_data['Salary'], errors='coerce')
salary_data = salary_data.drop_duplicates(subset=['Player'])
salary_data = salary_data.iloc[1:].reset_index(drop=True) # 移除第一列

# 清理 Stats 資料 (模仿 R 排序邏輯：將 2TM, 3TM 排到後面，然後去重)
stats_data['is_multi'] = stats_data['Team'].isin(["2TM", "3TM"])
stats_data = stats_data.sort_values(by=['PlayerID', 'is_multi'])
stats_data = stats_data.drop_duplicates(subset=['PlayerID'], keep='first')
stats_data = stats_data.drop(columns=['Player', 'Team', 'is_multi'])
stats_data = stats_data.iloc[1:].reset_index(drop=True)

# 清理 Adv 資料
adv_data['is_multi'] = adv_data['Team'].isin(["2TM", "3TM"])
adv_data = adv_data.sort_values(by=['PlayerID', 'is_multi'])
adv_data = adv_data.drop_duplicates(subset=['PlayerID'], keep='first')
cols_to_drop = ["Rk", "Player", "Age", "Team", "Pos", "G", "GS", "MP", "is_multi"]
adv_data_sub = adv_data.drop(columns=[c for c in cols_to_drop if c in adv_data.columns])
adv_data_sub = adv_data_sub.iloc[1:].reset_index(drop=True)

# 合併資料
merged_data = pd.merge(salary_data, stats_data, on="PlayerID", how="left")
merged_data = pd.merge(merged_data, adv_data_sub, on="PlayerID", how="left")

# 篩選有效列
clean_data = merged_data.dropna(subset=['Salary', 'MP']).copy()

# 計算進階數據
clean_data['Age_Sq'] = clean_data['Age'] ** 2

PSPP = 1.12
PAPP = 1.08
PPB = 2.24
DB = 0.05
LPPB = 2.30

clean_data['MIN_VAL'] = clean_data['MP']
clean_data['PTS_VAL'] = clean_data['PTS']
clean_data['REB_VAL'] = clean_data['TRB'] * (PSPP + DB)
clean_data['AST_VAL'] = clean_data['AST'] * PPB
clean_data['STL_VAL'] = clean_data['STL'] * (PSPP + PAPP)
clean_data['BLK_VAL'] = clean_data['BLK'] * LPPB
clean_data['TOV_VAL'] = -clean_data['TOV'] * (PSPP + PAPP)

clean_data['SPV'] = (clean_data['MIN_VAL'] + clean_data['PTS_VAL'] + clean_data['REB_VAL'] + 
                     clean_data['AST_VAL'] + clean_data['STL_VAL'] + clean_data['BLK_VAL'] + clean_data['TOV_VAL'])

clean_data['SPV_Offense'] = clean_data['MIN_VAL'] + clean_data['PTS_VAL'] + clean_data['AST_VAL'] - clean_data['TOV_VAL']
clean_data['SPV_Defense'] = clean_data['MIN_VAL'] + clean_data['REB_VAL'] + clean_data['STL_VAL'] + clean_data['BLK_VAL']

clean_data['SPV_per_min'] = (clean_data['PTS_VAL'] + clean_data['REB_VAL'] + clean_data['AST_VAL'] + 
                             clean_data['STL_VAL'] + clean_data['BLK_VAL'] + clean_data['TOV_VAL']) / clean_data['MP']

# 2. 分群 (K-Means)
kmeans = KMeans(n_clusters=3, random_state=123, n_init=10)
clean_data['cluster'] = kmeans.fit_predict(clean_data[['SPV']])

print("\n分群結果 (SPV):")
print(clean_data['cluster'].value_counts())

# SPV 分群平均值
cluster_summary = clean_data.groupby('cluster').agg(
    count=('SPV', 'size'),
    mean_SPV=('SPV', 'mean'),
    mean_SPV_Offense=('SPV_Offense', 'mean'),
    mean_SPV_Defense=('SPV_Defense', 'mean')
).reset_index()
print("\nSPV 分群平均值:")
print(cluster_summary)

# SPV_per_min 分群
kmeans_per_min = KMeans(n_clusters=3, random_state=123, n_init=10)
clean_data['cluster_per_min'] = kmeans_per_min.fit_predict(clean_data[['SPV_per_min']])

cluster_per_min_summary = clean_data.groupby('cluster_per_min').agg(
    count=('SPV_per_min', 'size'),
    mean_SPV_per_min=('SPV_per_min', 'mean')
).reset_index()
print("\nSPV_per_min 分群平均值:")
print(cluster_per_min_summary)

# 儲存清理後的資料供 Shiny/Streamlit 使用
clean_data.to_csv("clean_nba_data.csv", index=False)

# 3. 資料視覺化 (Matplotlib / Seaborn)
# 比較統整的圖
plt.figure(figsize=(10, 6))
sns.scatterplot(data=clean_data, x="SPV", y="Salary", hue="Team", palette="tab20")
plt.title("SPV 值與薪資關係")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 6))
sns.scatterplot(data=clean_data, x="SPV_Offense", y="SPV_Defense", hue="Team", palette="tab20")
plt.title("進攻 / 防守的 SPV 值")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# 繪製 Top 40 長條圖的輔助函數
def plot_top_40(data, col_name, title, color="lightblue"):
    top_40 = data.nlargest(40, col_name)
    plt.figure(figsize=(10, 8))
    # 這裡用 barplot 並指定橫向顯示
    sns.barplot(data=top_40, x=col_name, y="Player", color=color, edgecolor="black")
    plt.title(title)
    plt.xlabel(col_name)
    plt.ylabel("Player Name")
    plt.tight_layout()
    plt.show()

plot_top_40(clean_data, "SPV", "SPV top 40")
plot_top_40(clean_data, "SPV_Offense", "SPV Offense top 40", color="tan")
plot_top_40(clean_data, "SPV_Defense", "SPV Defense top 40", color="mediumpurple")
plot_top_40(clean_data, "SPV_per_min", "SPV_per_min top 40", color="cyan")