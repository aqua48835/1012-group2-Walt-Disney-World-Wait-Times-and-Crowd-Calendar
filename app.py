import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ---------------------- 页面基础配置 ----------------------
plt.rcParams['axes.unicode_minus'] = False
st.set_page_config(page_title="Disney Park Operations Dashboard", layout="wide")

st.title("Disney World Park Operation Dashboard | Created by Xiajingying")
st.caption("For: Park Operations Manager | Purpose: Adjust staffing & ride operating hours based on crowd levels")

st.markdown("""
**Data Notes**:
- Coverage Period: Jan 202X - Dec 202X (Kaggle Disney World Crowd Snapshot Data)
- Production Refresh Rate: Hourly (sync real-time crowd, weather, and event data)
""")

# ---------------------- 加载数据 ----------------------
@st.cache_data
def load_real_data():
    calendar_df = pd.read_csv("calendar_enriched.csv")
    ride_df = pd.read_csv("ride_stats.csv")
    park_df = pd.read_csv("park_stats.csv")

    calendar_df["date"] = pd.to_datetime(calendar_df["date"])
    if "timestamp" in ride_df.columns:
        ride_df["timestamp"] = pd.to_datetime(ride_df["timestamp"])
    if "date" in park_df.columns:
        park_df["date"] = pd.to_datetime(park_df["date"])

    min_date = calendar_df["date"].min()
    max_date = calendar_df["date"].max()
    return calendar_df, ride_df, park_df, min_date, max_date

calendar_df, ride_df, park_df, min_date, max_date = load_real_data()

# ---------------------- 侧边筛选器 ----------------------
st.sidebar.header("Operation Filters")
selected_dates = st.sidebar.date_input(
    "Select Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)
start_date = pd.to_datetime(selected_dates[0])
end_date = pd.to_datetime(selected_dates[1])

park_list = calendar_df["park_name"].unique()
selected_park = st.sidebar.selectbox("Select Target Park", park_list, index=0)

special_date_options = ["All Dates", "Weekends Only", "Holidays Only", "Special Events Only"]
selected_special_date = st.sidebar.selectbox("Special Date Filter", special_date_options, index=0)

# ---------------------- 数据过滤 ----------------------
filtered_calendar = calendar_df[
    (calendar_df["date"] >= start_date) &
    (calendar_df["date"] <= end_date) &
    (calendar_df["park_name"] == selected_park)
].copy()

if selected_special_date == "Weekends Only":
    filtered_calendar = filtered_calendar[filtered_calendar["is_weekend"] == True]
elif selected_special_date == "Holidays Only":
    filtered_calendar = filtered_calendar[filtered_calendar["is_holiday"] == True]
elif selected_special_date == "Special Events Only":
    filtered_calendar = filtered_calendar[filtered_calendar["has_special_event"] == True]

filtered_ride = ride_df[ride_df["park_name"] == selected_park].copy() if "park_name" in ride_df.columns else ride_df

# 空数据保护
if len(filtered_calendar) == 0:
    st.warning("⚠️ No data matches your filter selection. Please change date range, park or special date filter.")
    st.stop()

# ---------------------- KPI 板块 ----------------------
st.subheader("Core Operation KPIs")
col1, col2, col3 = st.columns(3)

avg_crowd = filtered_calendar["crowd_level_pct"].mean()
avg_operating_hours = (filtered_calendar["operating_minutes"].mean()) / 60

# ========== FIX: 先判断status列是否存在，不存在就替换成别的KPI ==========
total_rides = filtered_ride["ride_name"].nunique() if "ride_name" in filtered_ride.columns else 0
operation_rate = 0
if "status" in filtered_ride.columns:
    operational_rides = filtered_ride[filtered_ride["status"] == "operational"]["ride_name"].nunique()
    operation_rate = (operational_rides / total_rides) * 100 if total_rides > 0 else 0
else:
    # 没有status列，改用【平均等待时间】作为第三个KPI兜底
    if "wait_time_min" in filtered_ride.columns and len(filtered_ride) > 0:
        avg_wait = filtered_ride["wait_time_min"].mean()
    else:
        avg_wait = 0

with col1:
    st.metric("Avg Crowd Level (%)", f"{avg_crowd:.0f}%")
with col2:
    st.metric("Avg Daily Operating Hours", f"{avg_operating_hours:.1f} hrs")
with col3:
    if "status" in filtered_ride.columns:
        st.metric("Ride Operational Rate", f"{operation_rate:.0f}%")
    else:
        st.metric("Avg Ride Wait Time (min)", f"{avg_wait:.0f}")

# ---------------------- 决策推荐面板 ----------------------
st.subheader("Operation Recommendation")
if avg_crowd >= 70:
    st.error("🔴 HIGH CROWD ALERT: Average crowd level over 70%. Recommend: increase staff, extend ride hours, deploy crowd control team.")
elif avg_crowd >= 50:
    st.warning("🟡 MODERATE CROWD: Keep standard staffing schedule. Monitor for peak hours and special events.")
else:
    st.success("🟢 LOW CROWD: Reduce temporary staff, schedule maintenance for low-priority rides.")

# ---------------------- 图表1：客流趋势 ----------------------
st.subheader("Crowd Insights")
st.markdown(f"### {selected_park} Crowd Trend ({start_date.date()} to {end_date.date()})")
daily_crowd = filtered_calendar.groupby(filtered_calendar["date"].dt.date)["crowd_level_pct"].mean().reset_index()
daily_crowd["date"] = pd.to_datetime(daily_crowd["date"])

fig1, ax1 = plt.subplots(figsize=(12, 4))
ax1.plot(daily_crowd["date"], daily_crowd["crowd_level_pct"], marker="o", color="#1f77b4", linewidth=2)
ax1.axhline(y=70, color="red", linestyle="--", label="Operation Alert Threshold (70%)")
ax1.set_ylim(0, 100)
ax1.set_xlabel("Date")
ax1.set_ylabel("Avg Daily Crowd Level (%)")
ax1.legend()
ax1.grid(True, alpha=0.3)
st.pyplot(fig1)

# ---------------------- 图表2：分组对比（周末/活动） ----------------------
st.markdown(f"### Crowd Factor Analysis")
if "has_special_event" in filtered_calendar.columns and filtered_calendar["has_special_event"].sum() > 0:
    factor_crowd = filtered_calendar.groupby("has_special_event")["crowd_level_pct"].mean().reset_index()
    factor_crowd["has_special_event"] = factor_crowd["has_special_event"].map({True: "With Special Event", False: "No Special Event"})
    title = "Impact of Special Events on Crowd Level"
else:
    factor_crowd = filtered_calendar.groupby("is_weekend")["crowd_level_pct"].mean().reset_index()
    factor_crowd["is_weekend"] = factor_crowd["is_weekend"].map({True: "Weekend", False: "Weekday"})
    title = "Crowd Level: Weekend vs Weekday"

fig2, ax2 = plt.subplots(figsize=(8, 4))
bars = ax2.bar(factor_crowd.iloc[:,0], factor_crowd["crowd_level_pct"], color=["#ff7f0e", "#2ca02c"])
ax2.set_ylim(0,100)
ax2.set_ylabel("Average Crowd Level (%)")
ax2.set_title(title)
for bar in bars:
    h = bar.get_height()
    ax2.text(bar.get_x()+bar.get_width()/2, h+1, f"{h:.0f}%", ha="center")
st.pyplot(fig2)

# ---------------------- 热门设施等待时间表格（加列判断） ----------------------
st.markdown("### Top Rides: Average Wait Time")
if "wait_time_min" in filtered_ride.columns and "ride_name" in filtered_ride.columns:
    ride_wait = filtered_ride.groupby("ride_name")["wait_time_min"].mean().sort_values(ascending=False).head(8).reset_index()
    st.dataframe(ride_wait, use_container_width=True)
else:
    st.info("No ride wait time data available in this dataset.")

# ---------------------- 免责声明 ----------------------
st.markdown("""
---
**Data Disclaimer**:
1. This dashboard is based on Kaggle snapshot data. Production version will sync real-time crowd, weather, and event data hourly.
2. Crowd level (crowd_level_pct) is estimated based on park capacity; actual crowd may fluctuate due to temporary closures or extreme weather.
3. Special event data (has_special_event) does not include ad-hoc events. For real-time event info, refer to park announcements.
""")
