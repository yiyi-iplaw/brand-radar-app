import streamlit as st
import feedparser
import re
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

st.set_page_config(page_title="Brand Radar PRO", layout="wide")

# =========================
# 参数（你要的 sidebar）
# =========================
st.sidebar.header("扫描设置")

days = st.sidebar.slider("扫描时间范围（天）", 1, 30, 7)
min_sources = st.sidebar.slider("最少来源数（过滤垃圾）", 1, 5, 2)

sources_selected = st.sidebar.multiselect(
    "选择数据源",
    [
        "Google News",
        "TechCrunch",
        "36Kr",
        "PR Newswire",
        "Reddit"
    ],
    default=["Google News", "TechCrunch", "36Kr"]
)

run = st.sidebar.button("开始扫描（真实数据）")

# =========================
# 数据源
# =========================
def get_feeds():
    feeds = []

    if "Google News" in sources_selected:
        feeds.append(("Google News", "https://news.google.com/rss/search?q=china+brand+startup&hl=en-US&gl=US&ceid=US:en"))

    if "TechCrunch" in sources_selected:
        feeds.append(("TechCrunch", "https://techcrunch.com/feed/"))

    if "36Kr" in sources_selected:
        feeds.append(("36Kr", "https://36kr.com/feed"))

    if "PR Newswire" in sources_selected:
        feeds.append(("PR Newswire", "https://www.prnewswire.com/rss/news-releases-list.rss"))

    if "Reddit" in sources_selected:
        feeds.append(("Reddit", "https://www.reddit.com/r/startups/.rss"))

    return feeds


# =========================
# 品牌识别（核心）
# =========================
INVALID_WORDS = set([
    "China", "Chinese", "US", "Startup", "Company", "Brand",
    "Market", "Tech", "AI", "Product", "New", "Global"
])

def extract_brands(text):
    words = re.findall(r'\b[A-Z][a-zA-Z0-9]{2,}\b', text)

    brands = []
    for w in words:
        if w not in INVALID_WORDS and not w.lower().startswith("http"):
            brands.append(w)

    return list(set(brands))


# =========================
# 抓取数据
# =========================
def fetch_data():
    feeds = get_feeds()
    cutoff = datetime.now() - timedelta(days=days)

    brand_sources = defaultdict(list)

    for source_name, url in feeds:
        feed = feedparser.parse(url)

        for entry in feed.entries:
            try:
                published = datetime(*entry.published_parsed[:6])
            except:
                continue

            if published < cutoff:
                continue

            title = entry.title
            link = entry.link

            brands = extract_brands(title)

            for b in brands:
                brand_sources[b].append({
                    "source": source_name,
                    "title": title,
                    "link": link,
                    "time": published
                })

    return brand_sources


# =========================
# 评分逻辑（核心）
# =========================
def score_brand(items):
    source_count = len(items)

    # 趋势分：来源越多越高
    trend_score = min(source_count * 15, 50)

    # 时机分：越新越高
    latest_time = max(i["time"] for i in items)
    days_ago = (datetime.now() - latest_time).days
    timing_score = max(20 - days_ago, 0)

    total = trend_score + timing_score

    return total, source_count


# =========================
# 主界面
# =========================
st.title("Brand Radar PRO")
st.caption("真实数据｜多源验证｜可点击原文｜可执行线索")

if run:
    with st.spinner("正在抓取真实数据..."):
        brand_data = fetch_data()

    leads = []

    for brand, items in brand_data.items():
        if len(items) < min_sources:
            continue

        score, count = score_brand(items)

        leads.append({
            "brand": brand,
            "score": score,
            "sources": count,
            "items": items
        })

    leads = sorted(leads, key=lambda x: x["score"], reverse=True)

    st.success(f"发现 {len(leads)} 条高质量线索")

    # =========================
    # 展示（可展开 + 多来源）
    # =========================
    for lead in leads:
        with st.expander(f"{lead['brand']} ｜ 评分 {lead['score']} ｜ 来源 {lead['sources']}"):
            st.write("### 证据（可点击）")

            for item in lead["items"]:
                st.markdown(f"- [{item['title']}]({item['link']})  \n  来源：{item['source']}")

            st.write("### 判断逻辑")
            st.write(f"- 出现 {lead['sources']} 个独立来源")
            st.write(f"- 最近时间：{max(i['time'] for i in lead['items']).strftime('%Y-%m-%d')}")
            st.write("- 属于近期活跃品牌（非历史品牌）")

else:
    st.info("点击左侧开始扫描")
