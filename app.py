from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brand_radar.config import settings
from brand_radar.db import BrandRadarDB
from brand_radar.feeds import scan_queries
from brand_radar.models import ScanRequest
from brand_radar.scoring import build_lead_rows


st.set_page_config(page_title="Brand Radar", layout="wide")
st.title("Brand Radar")
st.caption("发现正在起势、可能存在美国商标布局空窗的中国品牌")


def _default_queries() -> str:
    return "\n".join(
        [
            "中国品牌 出海 融资",
            "中国 新消费 品牌 海外",
            "中国 骑行 品牌 北美",
            "中国 智能硬件 英文官网",
            "中国 新能源 参展 海外",
            "中国 户外 品牌 亚马逊",
        ]
    )


def _parse_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


db = BrandRadarDB(settings.db_path)

with st.sidebar:
    st.header("扫描参数")
    queries_text = st.text_area("查询词，每行一个", value=_default_queries(), height=180)
    lookback_days = st.slider("主窗口：过去多少天", min_value=30, max_value=180, value=90, step=15)
    accel_days = st.slider("加速窗口：过去多少天", min_value=7, max_value=60, value=30, step=1)
    max_results_per_query = st.slider("每个查询最多抓取多少条", min_value=10, max_value=100, value=30, step=10)
    market = st.selectbox("目标市场", ["us"], index=0)
    run_scan = st.button("Run scan", type="primary")

if run_scan:
    queries = _parse_lines(queries_text)
    if not queries:
        st.error("请至少输入一个查询词。")
    else:
        req = ScanRequest(
            queries=queries,
            lookback_days=lookback_days,
            accel_days=accel_days,
            max_results_per_query=max_results_per_query,
            market=market,
        )
        with st.spinner("正在抓取公开信号并生成线索..."):
            articles = scan_queries(req)
            lead_rows = build_lead_rows(articles, req)
            db.upsert_scan_results(lead_rows)
        st.success(f"扫描完成。共生成 {len(lead_rows)} 条线索。")

all_leads = db.get_leads()

if not all_leads.empty:
    st.subheader("线索总览")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Leads", int(len(all_leads)))
    c2.metric("平均总分", round(float(all_leads["total_score"].mean()), 1))
    c3.metric("A类窗口", int((all_leads["window_status"] == "A").sum()))
    c4.metric("需人工复核商标", int((all_leads["tm_review_needed"] == 1).sum()))

    display_cols = [
        "company_name",
        "brand_name",
        "industry",
        "total_score",
        "growth_score",
        "global_score",
        "tm_gap_score",
        "outreach_score",
        "window_status",
        "lead_reason",
    ]
    edited = st.dataframe(
        all_leads[display_cols].sort_values(by="total_score", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    csv_buffer = io.StringIO()
    all_leads.to_csv(csv_buffer, index=False)
    st.download_button(
        "导出 CSV",
        data=csv_buffer.getvalue().encode("utf-8-sig"),
        file_name="brand_radar_leads.csv",
        mime="text/csv",
    )

    st.subheader("查看单条线索")
    options = [
        f"{row.company_name or 'Unknown'} | {row.brand_name or '-'} | {row.total_score}"
        for row in all_leads.itertuples()
    ]
    selected = st.selectbox("选择线索", options=options)
    idx = options.index(selected)
    row = all_leads.iloc[idx]

    left, right = st.columns([1, 1])
    with left:
        st.markdown(f"### {row['company_name'] or 'Unknown company'}")
        st.write(f"**Brand:** {row['brand_name'] or '-'}")
        st.write(f"**Industry:** {row['industry']}")
        st.write(f"**Window:** {row['window_status']}")
        st.write(f"**Lead reason:** {row['lead_reason']}")
        st.write(f"**Outreach angle:** {row['outreach_angle']}")
        st.write(f"**Trademark note:** {row['tm_note']}")
        st.write(f"**Signals:** {row['signals']}" )

    with right:
        st.markdown("### Recommended outreach draft")
        st.text_area(
            "Draft",
            value=row["outreach_draft"],
            height=260,
        )
        if row["source_urls"]:
            st.markdown("### Sources")
            for url in str(row["source_urls"]).split("\n"):
                if url.strip():
                    st.markdown(f"- {url.strip()}")
else:
    st.info("还没有线索。先在左侧运行一次扫描。")
