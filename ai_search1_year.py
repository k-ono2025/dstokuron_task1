import feedparser
import pandas as pd
import time
from datetime import datetime
import matplotlib.pyplot as plt
from tqdm import tqdm
from urllib.parse import quote
import os

# 分野の指定（製造業は除外）
keywords = ["medical", "education", "chemistry", "environment"]
base_query = "artificial intelligence"
year_range = range(2010, 2025)
results_per_query = 1000

# 出力ディレクトリ作成
os.makedirs("csv_by_field", exist_ok=True)

# 論文情報を格納するリスト
data_records = []

# 分野ごとにデータ取得
for keyword in tqdm(keywords, desc="全分野処理中"):
    query = f'all:"{base_query}" AND all:"{keyword}"'
    encoded_query = quote(query)
    base_url = 'http://export.arxiv.org/api/query?'
    start = 0

    while True:
        url = f'{base_url}search_query={encoded_query}&start={start}&max_results=100'
        feed = feedparser.parse(url)

        if not feed.entries:
            break

        for entry in feed.entries:
            try:
                pub_date = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ')
                year = pub_date.year
                if year in year_range:
                    data_records.append({
                        "title": entry.title,
                        "summary": entry.summary,
                        "published": pub_date.date(),
                        "year": year,
                        "month": pub_date.strftime('%Y-%m'),
                        "category": keyword
                    })
            except Exception:
                continue

        start += 100
        time.sleep(3)

        if start >= results_per_query:
            break

# DataFrame化とソート
df = pd.DataFrame(data_records)
df = df.sort_values(by=["category", "year", "published"])

# 全体CSV保存（URL・journal_ref 含まず）
df.to_csv("ai_crossdomain_trend.csv", index=False)
print("✅ 全体CSV出力完了: ai_crossdomain_trend.csv")

# 分野別にCSVを出力
for keyword in keywords:
    df_field = df[df["category"] == keyword]
    df_field.to_csv(f"csv_by_field/ai_trend_{keyword}_summary_only.csv", index=False)
print("✅ 分野別CSV出力完了: ./csv_by_field/")

# 年単位の件数集計とグラフ
df["year"] = pd.to_datetime(df["published"]).dt.year
yearly_summary = df.groupby(["year", "category"]).size().reset_index(name="count")
pivot_yearly = yearly_summary.pivot(index="year", columns="category", values="count").fillna(0)
pivot_yearly = pivot_yearly.sort_index()

# 年単位折れ線グラフ描画
pivot_yearly.plot(marker='o', figsize=(10,6))
plt.title("AI × arXiv trend")
plt.xlabel("Year")
plt.ylabel("Number of Papers")
plt.grid(True)
plt.tight_layout()
plt.savefig("ai_trend_yearly_plot_summary_only.png")
plt.show()
