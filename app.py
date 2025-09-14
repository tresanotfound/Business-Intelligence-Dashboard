# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_prep import prepare_all

st.set_page_config(
    page_title="Marketing Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Load data (cached) ----------------
@st.cache_data(show_spinner=True)
def load_data():
    return prepare_all()

data = load_data()

# safe access to components
daily_total = data.get('daily_total', pd.DataFrame())
daily_channel = data.get('daily_channel', pd.DataFrame())
business = data.get('business', pd.DataFrame())
campaign_perf = data.get('campaign_perf', pd.DataFrame())
business_join = data.get('business_join', pd.DataFrame())
channels_raw = data.get('channels_raw', pd.DataFrame())

# ---------------- Styles / Helpers ----------------
def fmt_currency(x):
    try:
        return f"${x:,.0f}"
    except Exception:
        return x

def safe_sum(df, col):
    return float(df[col].sum()) if (isinstance(df, pd.DataFrame) and col is not None and col in df.columns) else 0.0

# ---------------- Sidebar Filters ----------------
st.sidebar.header("Filters")
min_date = daily_total['date'].min() if not daily_total.empty and 'date' in daily_total.columns else None
max_date = daily_total['date'].max() if not daily_total.empty and 'date' in daily_total.columns else None

if min_date is not None and max_date is not None:
    date_range = st.sidebar.date_input("Date range", [min_date, max_date])
else:
    date_range = None

available_channels = sorted(daily_channel['channel'].unique()) if not daily_channel.empty and 'channel' in daily_channel.columns else []
channels_selected = st.sidebar.multiselect("Channels", options=available_channels, default=available_channels)

states_selected = None
if 'state' in channels_raw.columns:
    states_selected = st.sidebar.multiselect("State / Region", options=sorted(channels_raw['state'].dropna().unique()), default=None)

# KPI period selection quick presets
st.sidebar.markdown("---")
period_choice = st.sidebar.selectbox("Quick period", ["Custom (date picker above)", "Last 7 days", "Last 30 days", "All time"])

# ---------------- Filter function ----------------
def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty or 'date' not in df.columns:
        return df

    out = df.copy()

    # Ensure all dates in df are Timestamps
    out['date'] = pd.to_datetime(out['date'])

    if date_range:
        # Ensure selected dates are also Timestamps
        start = pd.to_datetime(date_range[0])
        end = pd.to_datetime(date_range[1])
        out = out[(out['date'] >= start) & (out['date'] <= end)]

    if 'channel' in out.columns and channels_selected:
        out = out[out['channel'].isin(channels_selected)]

    if states_selected is not None and 'state' in out.columns and states_selected:
        out = out[out['state'].isin(states_selected)]

    return out


ft_daily_total = apply_filters(daily_total)
ft_daily_channel = apply_filters(daily_channel)
ft_campaign_perf = apply_filters(campaign_perf)
ft_business_join = apply_filters(business_join)
ft_channels_raw = apply_filters(channels_raw)
ft_business = apply_filters(business)

# ---------------- Top header ----------------
st.title("📊 Marketing Intelligence Dashboard")
st.markdown("Connect marketing spend & campaign performance to business outcomes (revenue, orders, profit).")
st.markdown("Use the **BI Guide** tab for design best-practices and real-world dashboard examples.")

# ---------------- Tabs ----------------
tab_overview, tab_channels, tab_advanced, tab_guide = st.tabs(["Overview", "Channel & Campaigns", "Advanced Analysis", "BI Guide"])

# ---------------- Overview Tab ----------------
with tab_overview:
    st.subheader("Overview & Key Metrics")

    # KPIs
    k_col1, k_col2, k_col3, k_col4, k_col5 = st.columns(5, gap="large")
    total_spend = safe_sum(ft_daily_total, 'spend')
    attributed_rev = safe_sum(ft_daily_total, 'attributed_revenue') if 'attributed_revenue' in ft_daily_total.columns else 0.0
    business_rev = safe_sum(ft_business_join, 'revenue') if 'revenue' in ft_business_join.columns else safe_sum(ft_business, 'revenue')
    total_clicks = int(safe_sum(ft_daily_total, 'clicks')) if 'clicks' in ft_daily_total.columns else "n/a"
    roas = attributed_rev / total_spend if total_spend > 0 else None

    k_col1.metric("Total Spend", fmt_currency(total_spend))
    k_col2.metric("Attributed Revenue", fmt_currency(attributed_rev))
    k_col3.metric("Business Revenue", fmt_currency(business_rev))
    k_col4.metric("ROAS", f"{roas:.2f}" if roas else "n/a")
    k_col5.metric("Total Clicks", f"{total_clicks}")

    st.markdown("---")

    # Trends combined chart
    st.subheader("Spend by Channel (stacked) with Business Revenue")

    if ft_daily_channel.empty:
        st.info("No marketing data available for the selected filters.")
    else:
        fig = go.Figure()
        # stacked spend per channel
        for ch in ft_daily_channel['channel'].unique():
            dfc = ft_daily_channel[ft_daily_channel['channel'] == ch].sort_values('date')
            fig.add_trace(go.Bar(
                x=dfc['date'], y=dfc['spend'], name=f"{ch} Spend", marker={'opacity':0.9}
            ))
        # overlay revenue as line on secondary axis if available
        if 'revenue' in ft_business_join.columns:
            fig.add_trace(go.Scatter(
                x=ft_business_join['date'], y=ft_business_join['revenue'],
                name="Business Revenue", mode="lines+markers",
                marker=dict(color='black'), yaxis="y2", line=dict(width=3)
            ))
            fig.update_layout(yaxis2=dict(title="Revenue", overlaying="y", side="right"))

        fig.update_layout(barmode='stack', xaxis_title="Date", yaxis_title="Spend (USD)", legend_title="Series", height=450)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("High-level Channel Breakdown")
    if ft_daily_channel.empty:
        st.info("No channel data to summarize.")
    else:
        summary = ft_daily_channel.groupby('channel').agg({
            'impression': 'sum', 'clicks': 'sum', 'spend': 'sum', 'attributed_revenue': 'sum'
        }).reset_index()
        # safe computations
        summary['ctr'] = summary['clicks'] / summary['impression']
        summary['cpc'] = summary['spend'] / summary['clicks']
        summary['roas'] = summary['attributed_revenue'] / summary['spend']
        st.dataframe(summary.sort_values('spend', ascending=False).style.format({
            'impression': '{:,.0f}', 'clicks': '{:,.0f}', 'spend': '${:,.0f}',
            'attributed_revenue': '${:,.0f}', 'ctr': '{:.2%}', 'cpc': '${:,.2f}', 'roas': '{:.2f}'
        }), use_container_width=True)

# ---------------- Channel & Campaigns Tab ----------------
with tab_channels:
    st.subheader("Channel & Campaign Performance")
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown("#### Campaign ROAS Distribution")
        if ft_campaign_perf.empty:
            st.info("No campaign-level data available.")
        else:
            dfcamp = ft_campaign_perf.copy()
            dfcamp = dfcamp[dfcamp['spend'] > 0] if 'spend' in dfcamp.columns else dfcamp
            fig_campaign = px.box(dfcamp, x='channel', y='roas', points="all", title="ROAS distribution by channel")
            st.plotly_chart(fig_campaign, use_container_width=True)

        st.markdown("#### Top 10 Campaigns by ROAS")
        if not ft_campaign_perf.empty and 'roas' in ft_campaign_perf.columns:
            top = ft_campaign_perf.sort_values('roas', ascending=False).head(10)[['campaign','channel','spend','attributed_revenue','roas','ctr','cpc']]
            st.dataframe(top.style.format({'spend':'${:,.0f}','attributed_revenue':'${:,.0f}','roas':'{:.2f}','ctr':'{:.2%}','cpc':'${:,.2f}'}), use_container_width=True)
        else:
            st.info("No campaign rows to show.")

    with c2:
        st.markdown("#### Channel Spend Share")
        if ft_daily_channel.empty:
            st.info("No data")
        else:
            spend_share = ft_daily_channel.groupby('channel').agg({'spend':'sum'}).reset_index()
            fig_pie = px.pie(spend_share, names='channel', values='spend', title='Spend Share by Channel', hole=0.45)
            st.plotly_chart(fig_pie, use_container_width=True)

# ---------------- Advanced Analysis Tab ----------------
with tab_advanced:
    st.subheader("Advanced analysis & export")

    st.markdown("### Lag Analysis (simple visualization)")
    if ft_daily_channel.empty or ft_business_join.empty:
        st.info("Not enough data to show lag analysis. Need marketing spend by date and business revenue by date.")
    else:
        # prepare daily totals (marketing)
        mk = ft_daily_channel.groupby('date').agg({'spend':'sum'}).reset_index().sort_values('date')
        bk = ft_business_join[['date','revenue']].drop_duplicates().sort_values('date') if 'revenue' in ft_business_join.columns else pd.DataFrame()
        if not bk.empty:
            merged = pd.merge(mk, bk, on='date', how='left').fillna(0)
            merged['spend_7d'] = merged['spend'].rolling(7, min_periods=1).sum()
            merged['revenue_7d'] = merged['revenue'].rolling(7, min_periods=1).sum()
            fig_lag = go.Figure()
            fig_lag.add_trace(go.Bar(x=merged['date'], y=merged['spend_7d'], name='7-day Spend'))
            fig_lag.add_trace(go.Scatter(x=merged['date'], y=merged['revenue_7d'], name='7-day Revenue', line=dict(color='black')))
            fig_lag.update_layout(title='7-day rolling Spend vs Revenue', xaxis_title='Date')
            st.plotly_chart(fig_lag, use_container_width=True)
        else:
            st.info("Business revenue not available to compute lag analysis.")

    st.markdown("---")
    st.markdown("### Export filtered data")
    if not ft_daily_channel.empty:
        st.download_button("Download filtered daily channel csv", data=ft_daily_channel.to_csv(index=False), file_name="daily_channel_filtered.csv")
    else:
        st.info("No data to export for the selected filters.")

# ---------------- BI Guide Tab ----------------
with tab_guide:
    st.header("Design Guide: 10 BI Dashboard Examples")
    st.markdown("""Unlocking Insights with Business Intelligence Dashboards...""")
    # (rest of your guide text unchanged)

# ---------------- Footer ----------------
st.markdown("---")
st.caption("Deliverables: Hosted BI dashboard link + Source repository. Built with Streamlit & Plotly.")
