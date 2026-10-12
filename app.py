import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ---------------------- 1. 页面基础配置（删除中文配置，避免方框） ----------------------
# 直接删除中文字体设置，图表用英文，避免Streamlit Cloud字体缺失问题
plt.rcParams['axes.unicode_minus'] = False  # 仅保留负号正常显示

# 页面标题+小组名称
st.title("Disney World Park Operation Dashboard | Group: 1012-group2")
# 单行说明：面向角色+核心决策
st.caption("For: Park Operations Manager | Purpose: Adjust staffing & ride hours based on real-time crowd levels")

# 数据周期+刷新频率标注
st.markdown(f"""
**Data Notes**:
- Coverage Period: Jan 202X - Dec 202X (Kaggle Disney World Crowd Snapshot Data)
- Production Refresh Rate: Hourly (sync real-time crowd, weather, and event data)
""", unsafe_allow_html=True)


# ---------------------- 2. 加载数据（基于真实CSV字段） ----------------------
@st.cache_data  # 缓存数据，提升页面速度
def load_real_data():
    calendar_df = pd.read_csv("calendar_enriched.csv")  # Calendar + crowd data
    ride_df = pd.read_csv("ride_stats.csv")              # Ride operation data
    park_df = pd.read_csv("park_stats.csv")              # Park visitor data

    # Standardize date format
    calendar_df["date"] = pd.to_datetime(calendar_df["date"])
    if "timestamp" in ride_df.columns:
        ride_df["timestamp"] = pd.to_datetime(ride_df["timestamp"])
    if "date" in park_df.columns:
        park_df["date"] = pd.to_datetime(park_df["date"])

    # Date range for filter
    min_date = calendar_df["date"].min()
    max_date = calendar_df["date"].max()

    return calendar_df, ride_df, park_df, min_date, max_date


# Load data
calendar_df, ride_df, park_df, min_date, max_date = load_real_data()


# ---------------------- 3. Filter Design（运营经理所需筛选器） ----------------------
st.sidebar.header("Operation Filters")

# 1. Date range filter
selected_dates = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)
start_date = pd.to_datetime(selected_dates[0])
end_date = pd.to_datetime(selected_dates[1])

# 2. Park filter
if "park_name" in calendar_df.columns:
    park_list = calendar_df["park_name"].unique()
    selected_park = st.sidebar.selectbox("Select Target Park", park_list, index=0)
else:
    selected_park = "Disney World Main Park"

# 3. Special date filter
special_date_options = ["All Dates", "Weekends Only", "Holidays Only", "Special Events Only"]
selected_special_date = st.sidebar.selectbox("Special Date Filter", special_date_options, index=0)


# ---------------------- 4. Data Filtering（数据过滤） ----------------------
# Basic filter: Date + Park
filtered_calendar = calendar_df[
    (calendar_df["date"] >= start_date) &
    (calendar_df["date"] <= end_date) &
    (calendar_df["park_name"] == selected_park)
].copy()

# Special date filter
if selected_special_date == "Weekends Only":
    filtered_calendar = filtered_calendar[filtered_calendar["is_weekend"] == True]
elif selected_special_date == "Holidays Only":
    filtered_calendar = filtered_calendar[filtered_calendar["is_holiday"] == True]
elif selected_special_date == "Special Events Only":
    filtered_calendar = filtered_calendar[filtered_calendar["has_special_event"] == True]

# Ride data filter
if "park_name" in ride_df.columns:
    filtered_ride = ride_df[ride_df["park_name"] == selected_park].copy()
else:
    filtered_ride = ride_df


# ---------------------- 5. Core KPI Calculation（核心KPI） ----------------------
st.subheader("Core Operation KPIs")
col1, col2, col3 = st.columns(3)

# KPI1: Average Crowd Level
avg_crowd = filtered_calendar["crowd_level_pct"].mean()
# Compare with previous week
prev_week_end = start_date - pd.Timedelta(days=1)
prev_week_start = prev_week_end - pd.Timedelta(days=len(filtered_calendar)-1)
prev_week_crowd = calendar_df[
    (calendar_df["date"] >= prev_week_start) &
    (calendar_df["date"] <= prev_week_end) &
    (calendar_df["park_name"] == selected_park)
]["crowd_level_pct"].mean()
crowd_change = avg_crowd - prev_week_crowd

with col1:
    st.metric(
        label="Avg Crowd Level (%)",
        value=f"{avg_crowd:.0f}%",
        delta=f"{crowd_change:.0f}% (vs Last Week)",
        delta_color="inverse"
    )

# KPI2: Avg Daily Operating Hours
avg_operating_hours = (filtered_calendar["operating_minutes"].mean()) / 60
with col2:
    st.metric(
        label="Avg Daily Operating Hours",
        value=f"{avg_operating_hours:.1f} hrs",
        delta=None
    )

# KPI3: Ride Operational Rate / Daily Visitors
with col3:
    if "status" in filtered_ride.columns and "ride_name" in filtered_ride.columns:
        total_rides = filtered_ride["ride_name"].nunique()
        operational_rides = filtered_ride[filtered_ride["status"] == "operational"]["ride_name"].nunique()
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
        avg_visitors = filtered_park["daily_visitors"].mean()
        st.metric(
            label="Avg Daily Visitors",
            value=f"{avg_visitors:.0f}",
            delta=None
        )


# ---------------------- 6. Supporting Charts（英文图表，无方框） ----------------------
st.subheader("Crowd Insights (Explain KPI Changes)")

# Chart 1: Crowd Level Trend Over Time
st.markdown(f"### {selected_park} Crowd Trend ({start_date.date()} to {end_date.date()})")
daily_crowd = filtered_calendar.groupby(filtered_calendar["date"].dt.date)["crowd_level_pct"].mean().reset_index()
daily_crowd["date"] = pd.to_datetime(daily_crowd["date"])

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(daily_crowd["date"], daily_crowd["crowd_level_pct"], marker="o", color="#1f77b4", linewidth=2)
# Add operation threshold line
ax.axhline(y=70, color="red", linestyle="--", label="Operation Alert Threshold (70%)")
# Mark weekends
for idx, row in daily_crowd.iterrows():
    is_weekend = filtered_calendar[filtered_calendar["date"].dt.date == row["date"].date()]["is_weekend"].iloc[0]
    if is_weekend:
        ax.scatter(row["date"], row["crowd_level_pct"], color="orange", s=80, zorder=5)

ax.set_xlabel("Date")
ax.set_ylabel("Avg Daily Crowd Level (%)")
ax.set_title(f"{selected_special_date} Crowd Level Trend")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# Chart 2: Crowd Level vs Special Events
st.markdown(f"### {selected_park} Crowd Factor Analysis")
event_crowd = filtered_calendar.groupby("has_special_event")["crowd_level_pct"].agg(["mean", "count"]).reset_index()
event_crowd["has_special_event"] = event_crowd["has_special_event"].map({True: "With Special Event", False: "No Special Event"})

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(event_crowd["has_special_event"], event_crowd["mean"], color=["#ff7f0e", "#2ca02c"])
ax.set_xlabel("Special Event Status")
ax.set_ylabel("Average Crowd Level (%)")
ax.set_title("Impact of Special Events on Crowd Level")

# Add value and sample count labels
for bar, count in zip(bars, event_crowd["count"]):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
            f"{height:.0f}%\n(n={count})", ha="center", va="bottom")

st.pyplot(fig)


# ---------------------- 7. Data Disclaimer（数据免责） ----------------------
st.markdown("""
---
**Data Disclaimer**:
1. This dashboard is based on Kaggle snapshot data. Production version will sync real-time crowd, weather, and event data hourly.
2. Crowd level (crowd_level_pct) is estimated based on park capacity; actual crowd may fluctuate due to temporary closures or extreme weather.
3. Special event data (has_special_event) does not include ad-hoc events. For real-time event info, refer to park announcements.
""", unsafe_allow_html=True)
