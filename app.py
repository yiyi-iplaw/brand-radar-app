import streamlit as st
import requests
import xml.etree.ElementTree as ET
import re

st.set_page_config(page_title="Brand Radar", layout="wide")

st.title("Brand Radar")
st.caption("真实品牌发现系统（每条结果可点击验证）")

# =========================
# 数据源（Google News RSS）
# =========================

RSS_SOURCES = [
    "https://news.google.com/rss/search?q=中国品牌+出海&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
    "https://news.google.com/rss/search?q=China+brand+overseas&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=新消费+品牌+融资&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
]

# =========================
# 品牌识别（可解释规则）
# =========================

def extract_brands(text):
    words = re.findall(r'\b[A-Za-z][A-Za-z0-9]{2,}\b', text)
    brands = []

    for w in words:
        if w[0].isupper():
            brands.append(w)

    return list(set(brands))


INVALID = ["China", "Chinese", "Brand", "Company", "Technology"]

KNOWN = ["anker", "ugreen", "miniso", "shein", "kkv", "baseus"]

def clean_brand(b):
    if any(x.lower() in b.lower() for x in INVALID):
        return False
    if b.lower() in KNOWN:
        return False
    if len(b) < 3:
        return False
    return True


# =========================
# 抓取 RSS（真实数据）
# =========================

def fetch_news():
    results = []

    for url in RSS_SOURCES:
        try:
            r = requests.get(url, timeout=10)
            root = ET.fromstring(r.content)

            for item in root.findall(".//item")[:20]:
                title = item.find("title").text
                link = item.find("link").text

                brands = extract_brands(title)

                for b in brands:
                    if clean_brand(b):
                        results.append({
                            "brand": b,
                            "title": title,
                            "url": link
                        })

        except:
            continue

    return results


# =========================
# 主逻辑
# =========================

if st.button("开始扫描（真实数据）"):

    with st.spinner("抓取真实新闻源..."):

        data = fetch_news()

    # 去重
    seen = set()
    unique = []

    for d in data:
        key = d["brand"] + d["url"]
        if key not in seen:
            seen.add(key)
            unique.append(d)

    st.success(f"发现 {len(unique)} 条真实线索")

    # =========================
    # 展示（完全可验证）
    # =========================

    for r in unique:
        with st.expander(f"{r['brand']}"):

            st.write("**来源标题：**")
            st.write(r["title"])

            st.write("**原始链接：**")
            st.markdown(f"[点击查看]({r['url']})")

            st.info("该品牌从真实新闻标题中提取，未进行任何推测性判断")
