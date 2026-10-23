import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ---------------------- 1. 页面基础配置（避免中文方框） ----------------------
plt.rcParams['axes.unicode_minus'] = False  # 确保负号正常显示

# 页面标题+小组名称
st.title("Disney World Park Operation Dashboard | Created by Xiajingying")
# 核心功能说明
st.caption("For: Park Operations Manager | Purpose: Adjust staffing & ride hours based on real-time crowd levels")

# 数据说明（替换202X为真实年份）
st.markdown(f"""
**Data Notes**:
- Coverage Period: Jan 202X - Dec 202X (Kaggle Disney World Crowd Snapshot Data)
- Production Refresh Rate: Hourly (sync real-time crowd, weather, and event data)
""", unsafe_allow_html=True)


# ---------------------- 2. 数据加载（适配真实CSV字段） ----------------------
@st.cache_data  # 缓存数据，提升加载速度
def load_real_data():
    # 加载核心数据集
    calendar_df = pd.read_csv("calendar_enriched.csv")  # 日历+客流数据
    ride_df = pd.read_csv("ride_stats.csv")              # 设施运营数据
    park_df = pd.read_csv("park_stats.csv")              # 园区访客数据

    # 统一日期格式
    calendar_df["date"] = pd.to_datetime(calendar_df["date"])
    if "timestamp" in ride_df.columns:
        ride_df["timestamp"] = pd.to_datetime(ride_df["timestamp"])
    if "date" in park_df.columns:
        park_df["date"] = pd.to_datetime(park_df["date"])

    # 提取日期范围（用于筛选器）
    min_date = calendar_df["date"].min()
    max_date = calendar_df["date"].max()

    return calendar_df, ride_df, park_df, min_date, max_date


# 执行数据加载
calendar_df, ride_df, park_df, min_date, max_date = load_real_data()


# ---------------------- 3. 筛选器设计（运营经理核心需求） ----------------------
st.sidebar.header("Operation Filters")

# 1. 日期范围筛选
selected_dates = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)
start_date = pd.to_datetime(selected_dates[0])
end_date = pd.to_datetime(selected_dates[1])

# 2. 园区筛选（适配多园区数据）
if "park_name" in calendar_df.columns:
    park_list = calendar_df["park_name"].unique()
    selected_park = st.sidebar.selectbox("Select Target Park", park_list, index=0)
else:
    selected_park = "Disney World Main Park"

# 3. 特殊日期筛选（聚焦高压力时段）
special_date_options = ["All Dates", "Weekends Only", "Holidays Only", "Special Events Only"]
selected_special_date = st.sidebar.selectbox("Special Date Filter", special_date_options, index=0)


# ---------------------- 4. 数据过滤（精准匹配筛选条件） ----------------------
# 基础过滤：日期+园区
filtered_calendar = calendar_df[
    (calendar_df["date"] >= start_date) &
    (calendar_df["date"] <= end_date) &
    (calendar_df["park_name"] == selected_park)
].copy()

# 特殊日期二次过滤
if selected_special_date == "Weekends Only":
    filtered_calendar = filtered_calendar[filtered_calendar["is_weekend"] == True]
elif selected_special_date == "Holidays Only":
    filtered_calendar = filtered_calendar[filtered_calendar["is_holiday"] == True]
elif selected_special_date == "Special Events Only":
    filtered_calendar = filtered_calendar[filtered_calendar["has_special_event"] == True]

# 设施数据过滤（匹配选中园区）
if "park_name" in ride_df.columns:
    filtered_ride = ride_df[ride_df["park_name"] == selected_park].copy()
else:
    filtered_ride = ride_df


# ---------------------- 5. 核心KPI计算（运营经理核心关注指标） ----------------------
st.subheader("Core Operation KPIs")
col1, col2, col3 = st.columns(3)  # 横向并列展示

# KPI1：平均客流拥挤度（核心指标）
avg_crowd = filtered_calendar["crowd_level_pct"].mean()
# 同比上周同期（体现数据对比价值）
prev_week_end = start_date - pd.Timedelta(days=1)
prev_week_start = prev_week_end - pd.Timedelta(days=len(filtered_calendar)-1)
prev_week_crowd = calendar_df[
    (calendar_df["date"] >= prev_week_start) &
    (calendar_df["date"] <= prev_week_end) &
    (calendar_df["park_name"] == selected_park)
]["crowd_level_pct"].mean() if len(calendar_df[
    (calendar_df["date"] >= prev_week_start) &
    (calendar_df["date"] <= prev_week_end) &
    (calendar_df["park_name"] == selected_park)
]) > 0 else 0
crowd_change = avg_crowd - prev_week_crowd

with col1:
    st.metric(
        label="Avg Crowd Level (%)",
        value=f"{avg_crowd:.0f}%",
        delta=f"{crowd_change:.0f}% (vs Last Week)",
        delta_color="inverse"  # 拥挤度上升显红色，下降显绿色
    )

# KPI2：园区日均开放时长
avg_operating_hours = (filtered_calendar["operating_minutes"].mean()) / 60 if filtered_calendar["operating_minutes"].notna().sum() > 0 else 0
with col2:
    st.metric(
        label="Avg Daily Operating Hours",
        value=f"{avg_operating_hours:.1f} hrs",
        delta=None
    )

# KPI3：设施正常运行率 / 日均入园人数（二选一，适配数据）
with col3:
    if "status" in filtered_ride.columns and "ride_name" in filtered_ride.columns:
        total_rides = filtered_ride["ride_name"].nunique()
        operational_rides = filtered_ride[filtered_ride["status"] == "operational"]["ride_name"].nunique() if filtered_ride["status"].notna().sum() > 0 else 0
        operation_rate = (operational_rides / total_rides) * 100 if total_rides > 0 else 0
        st.metric(
            label="Ride Operational Rate",
            value=f"{operation_rate:.0f}%",
            delta=None
        )
    elif "daily_visitors" in park_df.columns:
        filtered_park = park_df[
            (park_df["date"] >= start_date) &
            (park_df["date"] <= end_date) &
            (park_df["park_name"] == selected_park)
        ]
        avg_visitors = filtered_park["daily_visitors"].mean() if filtered_park["daily_visitors"].notna().sum() > 0 else 0
        st.metric(
            label="Avg Daily Visitors",
            value=f"{avg_visitors:.0f}",
            delta=None
        )


# ---------------------- 6. 辅助图表（解释KPI变动原因，无空白风险） ----------------------
st.subheader("Crowd Insights (Explain KPI Changes)")

# 图表1：客流拥挤度时间趋势（按日期）
st.markdown(f"### {selected_park} Crowd Trend ({start_date.date()} to {end_date.date()})")
# 按日期分组计算日均拥挤度
daily_crowd = filtered_calendar.groupby(filtered_calendar["date"].dt.date)["crowd_level_pct"].mean().reset_index()
daily_crowd["date"] = pd.to_datetime(daily_crowd["date"])

fig1, ax1 = plt.subplots(figsize=(12, 4))
# 绘制趋势线
ax1.plot(daily_crowd["date"], daily_crowd["crowd_level_pct"], marker="o", color="#1f77b4", linewidth=2)
# 添加运营警戒阈值线（70%）
ax1.axhline(y=70, color="red", linestyle="--", label="Operation Alert Threshold (70%)")
# 标注周末（橙色点）
for idx, row in daily_crowd.iterrows():
    date_match = filtered_calendar[filtered_calendar["date"].dt.date == row["date"].date()]
    if len(date_match) > 0 and date_match["is_weekend"].iloc[0]:
        ax1.scatter(row["date"], row["crowd_level_pct"], color="orange", s=80, zorder=5)

# 固定y轴范围（0-100%，符合拥挤度逻辑）
ax1.set_ylim(0, 100)
ax1.set_xlabel("Date")
ax1.set_ylabel("Avg Daily Crowd Level (%)")
ax1.set_title(f"{selected_special_date} Crowd Level Trend")
ax1.legend()
ax1.grid(True, alpha=0.3)
st.pyplot(fig1)

# 图表2：客流影响因素分析（特殊活动/周末二选一，避免空白）
st.markdown(f"### {selected_park} Crowd Factor Analysis")
# 优先用特殊活动数据，无数据则切换为周末vs工作日
if "has_special_event" in filtered_calendar.columns and filtered_calendar["has_special_event"].notna().sum() > 0:
    # 按特殊活动分组
    factor_crowd = filtered_calendar.groupby("has_special_event")["crowd_level_pct"].agg(["mean", "count"]).reset_index()
    factor_crowd["has_special_event"] = factor_crowd["has_special_event"].map({True: "With Special Event", False: "No Special Event"})
    x_label = "Special Event Status"
    title = "Impact of Special Events on Crowd Level"
else:
    # 按周末/工作日分组（兜底方案）
    factor_crowd = filtered_calendar.groupby("is_weekend")["crowd_level_pct"].agg(["mean", "count"]).reset_index()
    factor_crowd["is_weekend"] = factor_crowd["is_weekend"].map({True: "Weekend", False: "Weekday"})
    x_label = "Day Type"
    title = "Crowd Level: Weekend vs Weekday"

# 绘制柱状图
fig2, ax2 = plt.subplots(figsize=(8, 4))
bars = ax2.bar(factor_crowd[factor_crowd.columns[0]], factor_crowd["mean"], color=["#ff7f0e", "#2ca02c"])
# 固定y轴范围（0-100%）
ax2.set_ylim(0, 100)
ax2.set_xlabel(x_label)
ax2.set_ylabel("Average Crowd Level (%)")
ax2.set_title(title)

# 在柱子上标注数值和样本量
for bar, count in zip(bars, factor_crowd["count"]):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
             f"{height:.0f}%\n(n={count})", ha="center", va="bottom")

st.pyplot(fig2)


# ---------------------- 7. 数据免责声明（规避误导风险） ----------------------
st.markdown("""
---
**Data Disclaimer**:
1. This dashboard is based on Kaggle snapshot data. Production version will sync real-time crowd, weather, and event data hourly.
2. Crowd level (crowd_level_pct) is estimated based on park capacity; actual crowd may fluctuate due to temporary closures or extreme weather.
3. Special event data (has_special_event) does not include ad-hoc events. For real-time event info, refer to park announcements.
""", unsafe_allow_html=True)
