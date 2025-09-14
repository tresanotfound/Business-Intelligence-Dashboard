# data_prep.py
import pandas as pd
import numpy as np
from typing import Tuple, Dict

CHANNEL_FILES = {
    "Google": "data/Google.csv",
    "Facebook": "data/Facebook.csv",
    "TikTok": "data/TikTok.csv",
}
BUSINESS_FILE = "data/business.csv"

def _safe_div(n, d):
    return np.where(d==0, np.nan, n / d)

def load_and_standardize_channel(path: str, channel_name: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # lowercase columns for consistent references
    df.columns = [c.strip() for c in df.columns]
    # standardize names if different
    # look for common columns; rename to canonical names
    rename_map = {}
    cols_lower = [c.lower() for c in df.columns]
    if 'date' not in cols_lower:
        # attempt to find a date-like column
        for c in df.columns:
            if 'date' in c.lower():
                rename_map[c] = 'date'
    # common heuristics
    for c in df.columns:
        lc = c.lower()
        if 'impress' in lc:
            rename_map[c] = 'impression'
        elif lc == 'clicks' or 'click'==lc:
            rename_map[c] = 'clicks'
        elif 'spend' in lc or 'cost' in lc:
            rename_map[c] = 'spend'
        elif 'revenue' in lc or 'attributed revenue' in lc or 'attributed_revenue' in lc:
            rename_map[c] = 'attributed_revenue'
        elif 'campaign' in lc:
            rename_map[c] = 'campaign'
        elif 'tactic' in lc:
            rename_map[c] = 'tactic'
        elif 'state' in lc or 'region' in lc:
            rename_map[c] = 'state'
    df = df.rename(columns=rename_map)
    # Ensure expected columns exist
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    else:
        raise ValueError(f"Couldn't find a date column in {path}")
    # numeric conversions
    for col in ['impression', 'clicks', 'spend', 'attributed_revenue']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # set missing numeric -> 0 where appropriate
    if 'impression' in df.columns:
        df['impression'] = df['impression'].fillna(0)
    if 'clicks' in df.columns:
        df['clicks'] = df['clicks'].fillna(0)
    if 'spend' in df.columns:
        df['spend'] = df['spend'].fillna(0.0)
    if 'attributed_revenue' in df.columns:
        df['attributed_revenue'] = df['attributed_revenue'].fillna(0.0)

    df['channel'] = channel_name
    # Derived metrics per-row
    if 'impression' in df.columns and 'clicks' in df.columns:
        df['ctr'] = _safe_div(df['clicks'], df['impression'])
    else:
        df['ctr'] = np.nan
    if 'spend' in df.columns and 'clicks' in df.columns:
        df['cpc'] = _safe_div(df['spend'], df['clicks'])
    else:
        df['cpc'] = np.nan
    if 'spend' in df.columns and 'impression' in df.columns:
        df['cpm'] = _safe_div(df['spend'] * 1000, df['impression'])
    else:
        df['cpm'] = np.nan
    if 'attributed_revenue' in df.columns and 'spend' in df.columns:
        df['roas'] = _safe_div(df['attributed_revenue'], df['spend'])
    else:
        df['roas'] = np.nan
    return df

def load_all_channels(files: Dict[str, str]=CHANNEL_FILES) -> pd.DataFrame:
    dfs = []
    for channel, path in files.items():
        df = load_and_standardize_channel(path, channel)
        dfs.append(df)
    all_df = pd.concat(dfs, ignore_index=True, sort=False)
    # normalize campaign string
    if 'campaign' in all_df.columns:
        all_df['campaign'] = all_df['campaign'].astype(str).str.strip()
    if 'tactic' in all_df.columns:
        all_df['tactic'] = all_df['tactic'].astype(str).str.strip()
    return all_df

def load_business(path: str = BUSINESS_FILE) -> pd.DataFrame:
    # read csv
    df = pd.read_csv(path)

    # clean column names
    df.columns = df.columns.str.strip()

    # ensure date column
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    else:
        raise ValueError("No 'date' column found in business.csv")

    # rename columns to standard names
    rename_map = {
        '# of orders': 'orders',
        '# of new orders': 'new_orders',
        'new customers': 'customers',
        'total revenue': 'revenue',
        'gross profit': 'profit',
        'COGS': 'cogs'
    }
    df = df.rename(columns=rename_map)

    # convert numeric columns safely
    numeric_cols = ['orders', 'new_orders', 'customers', 'revenue', 'profit', 'cogs']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df


def aggregate_daily_channel(df: pd.DataFrame) -> pd.DataFrame:
    agg_cols = {
        'impression': 'sum',
        'clicks': 'sum',
        'spend': 'sum',
        'attributed_revenue': 'sum'
    }
    # only include columns present
    agg_cols = {k:v for k,v in agg_cols.items() if k in df.columns}
    group = df.groupby(['date', 'channel']).agg(agg_cols).reset_index()
    # recompute metrics
    group['ctr'] = _safe_div(group.get('clicks',0), group.get('impression',0))
    group['cpc'] = _safe_div(group.get('spend',0), group.get('clicks',0))
    group['cpm'] = _safe_div(group.get('spend',0) * 1000, group.get('impression',0))
    group['roas'] = _safe_div(group.get('attributed_revenue',0), group.get('spend',0))
    return group

def prepare_all() -> dict:
    channels = load_all_channels()
    business = load_business()
    daily_channel = aggregate_daily_channel(channels)
    # total daily across channels
    daily_total = daily_channel.groupby('date').agg({
        'impression':'sum', 'clicks':'sum', 'spend':'sum', 'attributed_revenue':'sum'
    }).reset_index()
    daily_total['ctr'] = _safe_div(daily_total['clicks'], daily_total['impression'])
    daily_total['cpc'] = _safe_div(daily_total['spend'], daily_total['clicks'])
    daily_total['cpm'] = _safe_div(daily_total['spend'] * 1000, daily_total['impression'])
    daily_total['roas'] = _safe_div(daily_total['attributed_revenue'], daily_total['spend'])
    # join to business (left)
    business_join = business.merge(daily_total, on='date', how='left', suffixes=('_biz','_marketing'))
    # rolling metrics
    business_join = business_join.sort_values('date')
    business_join['spend_7d'] = business_join['spend'].rolling(7, min_periods=1).sum()
    business_join['revenue_7d'] = business_join['revenue'].rolling(7, min_periods=1).sum() if 'revenue' in business_join.columns else np.nan
    # top campaigns
    if 'campaign' in channels.columns:
        campaign_perf = channels.groupby(['campaign','channel']).agg({
            'impression':'sum', 'clicks':'sum', 'spend':'sum', 'attributed_revenue':'sum'
        }).reset_index()
        campaign_perf['ctr'] = _safe_div(campaign_perf['clicks'], campaign_perf['impression'])
        campaign_perf['cpc'] = _safe_div(campaign_perf['spend'], campaign_perf['clicks'])
        campaign_perf['roas'] = _safe_div(campaign_perf['attributed_revenue'], campaign_perf['spend'])
    else:
        campaign_perf = pd.DataFrame()
    return {
        'channels_raw': channels,
        'daily_channel': daily_channel,
        'daily_total': daily_total,
        'business': business,
        'business_join': business_join,
        'campaign_perf': campaign_perf
    }

if __name__ == "__main__":
    d = prepare_all()
    print("Prepared datasets:", list(d.keys()))
