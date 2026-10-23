# Walt Disney World Wait Times & Crowd Calendar Dashboard
> BANA409 Assignment 4 Part 1: Data App

## Deployed App URL
https://1012-group2-walt-disney-world-wait-times-and-crowd-calendar-ob.streamlit.app/

## Project Overview
This Streamlit dashboard is built for Disney park decision-makers and park planners. It lets users explore historical crowd levels, ride wait times and calendar trends across Walt Disney World parks. The dashboard supports filtering by park, date range, and ride to identify busy seasons, peak hours, and rides with unstable wait times.

## Data Sources
- `calendar_enriched.csv`: Daily park calendar, crowd index, date features (holiday, weekend, season)
- `park_stats.csv`: Aggregated daily park-level crowd statistics
- `ride_stats.csv`: Individual ride historical wait time records

## How to Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
给你直接可用的 README.md（适配你这个 Disney 等待时间看板，满足 Assignment4 Part1 要求，包含Design Decisions，老师重点要看这个）
复制全部，粘贴到你的 README.md 里，直接替换原来那一行标题。
markdown
# Walt Disney World Wait Times & Crowd Calendar Dashboard
> BANA409 Assignment 4 Part 1: Data App

## Deployed App URL
https://1012-group2-walt-disney-world-wait-times-and-crowd-calendar-ob.streamlit.app/

## Project Overview
This Streamlit dashboard is built for Disney park decision-makers and park planners. It lets users explore historical crowd levels, ride wait times and calendar trends across Walt Disney World parks. The dashboard supports filtering by park, date range, and ride to identify busy seasons, peak hours, and rides with unstable wait times.

## Data Sources
- `calendar_enriched.csv`: Daily park calendar, crowd index, date features (holiday, weekend, season)
- `park_stats.csv`: Aggregated daily park-level crowd statistics
- `ride_stats.csv`: Individual ride historical wait time records

## How to Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
Design Decisions (Required for the assignment)
1. Target decision-maker
The audience is Disney park operations managers. They need to allocate staff, schedule maintenance, and plan special events to manage crowd pressure. They care about when crowds are high, which rides have long waits, and how wait times change by season/holiday.
2. Layout & Sidebar Filters
I put all interactive filters (park selection, date range, ride picker) in the sidebar. This keeps the main page clean for charts and tables. The filters are linked: after selecting a park, the ride dropdown only shows rides inside that park to avoid invalid selections.
3. Chart choices
Time-series line chart: Daily crowd index over the selected date range. Good for seeing long-term seasonal trends and holiday spikes.
Ride wait time distribution: Histogram to show how often a ride has very long waits. Useful for maintenance scheduling.
Summary table: Aggregated statistics (average wait, max wait, sample count) for quick comparison between rides.
4. Tradeoffs I made
I did not add complex forecasting in this dashboard. The decision-maker’s immediate need is to explore historical patterns, not predictions. Adding forecast would make the dashboard slower and harder to interpret.
I capped the date range to avoid loading too many rows at once. This prevents slowdowns on the free Streamlit community hosting.
I chose simple, readable charts instead of many fancy visualizations, so non-technical park managers can understand the insights quickly.
5. What the dashboard helps the stakeholder do
Identify high-crowd dates to arrange extra staff.
Find rides with consistently long waits for capacity improvements.
Compare crowd levels on holidays vs normal weekends.
