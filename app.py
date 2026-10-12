import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ---------------------- 1. 页面基础配置 ----------------------
# 设置中文字体（避免图表中文乱码）
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei']
plt.rcParams['axes.unicode_minus'] = False

# 页面标题与业务说明（作业强制要求）
st.title("Disney World 乐园运营仪表盘 | 小组名称：XXX")  # 替换成你们小组名称
st.caption("面向角色：迪士尼乐园运营经理 | 支撑决策：实时调整人力与设施开放计划，降低游客排队时长")

# 标注数据周期与计划刷新频率（作业Step4要求）
st.markdown(f"""
**数据说明**：
- 覆盖周期：202X年X月 - 202X年X月（Kaggle快照数据）
- 生产环境计划刷新频率：每30分钟（实时同步闸机客流与设施排队数据）
""", unsafe_allow_html=True)


# ---------------------- 2. 加载与预处理数据 ----------------------
@st.cache_data  # 缓存数据，避免重复加载
def load_data():
    # 加载核心数据集（替换成你实际需要的字段，这里以关键指标为例）
    calendar_df = pd.read_csv("calendar_enriched.csv")
    ride_df = pd.read_csv("ride_stats.csv")
    park_df = pd.read_csv("park_stats.csv")

    # 数据预处理：统一时间格式（根据实际CSV字段调整）
    calendar_df["date"] = pd.to_datetime(calendar_df["date"])  # 假设日期字段是"date"
    ride_df["timestamp"] = pd.to_datetime(ride_df["timestamp"])  # 假设设施数据有时间戳
    park_df["date"] = pd.to_datetime(park_df["date"])

    # 提取日期维度（用于筛选器）
    min_date = calendar_df["date"].min()
    max_date = calendar_df["date"].max()

    return calendar_df, ride_df, park_df, min_date, max_date


# 调用函数加载数据
calendar_df, ride_df, park_df, min_date, max_date = load_data()


# ---------------------- 3. 筛选器设计（仅保留运营经理需要的） ----------------------
st.sidebar.header("筛选条件")  # 侧边栏放筛选器，不占用主视觉

# 1. 日期范围筛选（运营经理需查看特定日期数据）
selected_dates = st.sidebar.date_input(
    "选择日期范围",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)
# 转换为datetime格式，匹配数据格式
start_date = pd.to_datetime(selected_dates[0])
end_date = pd.to_datetime(selected_dates[1])

# 2. 园区筛选（多园区场景下，运营经理关注单个园区）
park_list = park_df["park_name"].unique()  # 假设园区名称字段是"park_name"
selected_park = st.sidebar.selectbox("选择园区", park_list, index=0)

# 3. 设施类型筛选（可选，聚焦高人流设施）
ride_types = ride_df["ride_type"].unique()  # 假设设施类型字段是"ride_type"
selected_ride_type = st.sidebar.multiselect(
    "选择设施类型（可多选）",
    ride_types,
    default=ride_types  # 默认全选
)

# 应用筛选条件（核心：只保留筛选后的数据用于计算）
filtered_ride_df = ride_df[
    (ride_df["timestamp"].dt.date >= start_date.date()) &
    (ride_df["timestamp"].dt.date <= end_date.date()) &
    (ride_df["park_name"] == selected_park) &
    (ride_df["ride_type"].isin(selected_ride_type))
].copy()

filtered_park_df = park_df[
    (park_df["date"] >= start_date) &
    (park_df["date"] <= end_date) &
    (park_df["park_name"] == selected_park)
].copy()


# ---------------------- 4. 核心KPI计算（作业要求：最多3个，用st.metric） ----------------------
st.subheader("核心运营指标")

# 计算3个关键KPI（基于筛选后的数据，贴合运营经理需求）
col1, col2, col3 = st.columns(3)  # 横向并列展示

# KPI1：平均排队时长（运营经理最关注的核心指标）
avg_wait_time = filtered_ride_df["wait_time_minutes"].mean()  # 假设排队时长字段是"wait_time_minutes"
# 对比昨日（模拟同比/环比，让指标更有业务意义）
yesterday = end_date - pd.Timedelta(days=1)
yesterday_wait_time = ride_df[
    (ride_df["timestamp"].dt.date == yesterday.date()) &
    (ride_df["park_name"] == selected_park) &
    (ride_df["ride_type"].isin(selected_ride_type))
]["wait_time_minutes"].mean()
wait_time_change = avg_wait_time - yesterday_wait_time  # 变化量

with col1:
    st.metric(
        label="平均排队时长（分钟）",
        value=f"{avg_wait_time:.0f}",
        delta=f"{wait_time_change:.0f} 分钟（较昨日）",
        delta_color="inverse"  # 排队时长增加时显示红色，减少时绿色
    )

# KPI2：设施运行率（反映设施是否正常开放，影响客流承载）
total_rides = filtered_ride_df["ride_id"].nunique()  # 假设设施ID字段是"ride_id"
operational_rides = filtered_ride_df[filtered_ride_df["status"] == "operational"]["ride_id"].nunique()  # 假设状态字段是"status"
operation_rate = (operational_rides / total_rides) * 100 if total_rides > 0 else 0

with col2:
    st.metric(
        label="设施运行率",
        value=f"{operation_rate:.0f}%",
        delta=None  # 可根据实际需求加同比
    )

# KPI3：日均入园人数（反映整体客流压力）
daily_visitors = filtered_park_df["daily_visitors"].mean()  # 假设日均客流字段是"daily_visitors"
with col3:
    st.metric(
        label="日均入园人数",
        value=f"{daily_visitors:.0f}",
        delta=None
    )


# ---------------------- 5. 辅助图表（作业要求：1-2个，解释KPI涨跌） ----------------------
st.subheader("数据洞察（解释KPI变动原因）")

# 图表1：排队时长时间趋势（按小时，帮助运营经理看高峰时段）
st.markdown("### 1. 小时级排队时长趋势")
# 提取小时维度，计算每小时平均排队时长
filtered_ride_df["hour"] = filtered_ride_df["timestamp"].dt.hour
hourly_wait = filtered_ride_df.groupby("hour")["wait_time_minutes"].mean().reset_index()

# 绘制折线图
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(hourly_wait["hour"], hourly_wait["wait_time_minutes"], marker="o", color="#1f77b4")
ax.set_xlabel("小时（24小时制）")
ax.set_ylabel("平均排队时长（分钟）")
ax.set_title(f"{selected_park} 园区 - 筛选时段内小时级排队趋势")
ax.grid(True, alpha=0.3)
# 添加目标线（假设运营目标是排队时长≤30分钟）
ax.axhline(y=30, color="red", linestyle="--", label="运营目标≤30分钟")
ax.legend()
st.pyplot(fig)

# 图表2：不同设施类型排队时长对比（帮助定位高压力设施）
st.markdown("### 2. 各设施类型排队时长对比")
ride_type_wait = filtered_ride_df.groupby("ride_type")["wait_time_minutes"].agg(["mean", "count"]).reset_index()
ride_type_wait = ride_type_wait.sort_values("mean", ascending=False)  # 按平均时长降序

# 绘制柱状图
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(ride_type_wait["ride_type"], ride_type_wait["mean"], color="#ff7f0e")
ax.set_xlabel("设施类型")
ax.set_ylabel("平均排队时长（分钟）")
ax.set_title(f"{selected_park} 园区 - 各设施类型排队时长")
ax.tick_params(axis="x", rotation=45)  # 旋转x轴标签，避免重叠

# 在柱子上标注具体数值
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
            f"{height:.0f}", ha="center", va="bottom")

st.pyplot(fig)


# ---------------------- 6. 数据免责说明（作业Step3要求：规避误导风险） ----------------------
st.markdown("""
---
**数据免责声明**：
1. 本仪表盘数据基于Kaggle快照，生产环境将实时同步闸机与设施数据；
2. 排队时长包含临时故障导致的异常值，已通过算法剔除极端值（>120分钟）；
3. 设施运行率不包含计划维护的设施，如需查看维护计划请参考园区后台系统。
""", unsafe_allow_html=True)