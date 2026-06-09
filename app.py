import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

CSV_FILE = Path(__file__).parent / "A股总市值每日记录.csv"

st.set_page_config(
    page_title="A股总市值监控系统",
    layout="wide"
)

st.title("A股总市值监控系统")

if not CSV_FILE.exists():
    st.warning("桌面尚未找到 A股总市值每日记录.csv")
    st.stop()

df = pd.read_csv(CSV_FILE)

if len(df) == 0:
    st.error("CSV文件为空")
    st.stop()

# 处理交易日期：CSV里是 20260609 这种格式
df["交易日期"] = df["交易日期"].astype(str)
df["交易日期_dt"] = pd.to_datetime(
    df["交易日期"],
    format="%Y%m%d",
    errors="coerce"
)

df = df.dropna(subset=["交易日期_dt"])
df = df.sort_values("交易日期_dt").reset_index(drop=True)

if len(df) == 0:
    st.error("交易日期格式无法识别")
    st.stop()

latest = df.iloc[-1]

if len(df) >= 2:
    prev = df.iloc[-2]
else:
    prev = latest


def pct_change(col):
    if prev[col] == 0:
        return "0.00%"

    pct = (latest[col] - prev[col]) / prev[col] * 100
    return f"{pct:.2f}%"


st.subheader(
    f"最新数据（{latest['交易日期_dt'].strftime('%Y-%m-%d')}）"
)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "上证总市值",
    f"{latest['上证总市值_亿元']:,.0f}亿元",
    pct_change("上证总市值_亿元")
)

c2.metric(
    "深证总市值",
    f"{latest['深证总市值_亿元']:,.0f}亿元",
    pct_change("深证总市值_亿元")
)

c3.metric(
    "创业板总市值",
    f"{latest['创业板总市值_亿元']:,.0f}亿元",
    pct_change("创业板总市值_亿元")
)

c4.metric(
    "科创板总市值",
    f"{latest['科创板总市值_亿元']:,.0f}亿元",
    pct_change("科创板总市值_亿元")
)

st.subheader("历史数据")

show_df = df.drop(columns=["交易日期_dt"]).copy()
show_df["交易日期"] = pd.to_datetime(
    show_df["交易日期"],
    format="%Y%m%d",
    errors="coerce"
).dt.strftime("%Y-%m-%d")

st.dataframe(
    show_df,
    width="stretch"
)

cols = [
    "上证总市值_亿元",
    "深证总市值_亿元",
    "创业板总市值_亿元",
    "科创板总市值_亿元"
]

for col in cols:
    fig = px.line(
        df,
        x="交易日期_dt",
        y=col,
        markers=True,
        title=col
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )