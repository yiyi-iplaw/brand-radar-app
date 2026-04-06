import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="Brand Radar", layout="wide")

st.title("Brand Radar")
st.caption("基于真实数据源的品牌发现工具（每条线索可点击验证）")

# ------------------------
# 工具函数
# ------------------------

def extract_brands(text):
    words = re.findall(r'\b[A-Za-z][A-Za-z0-9]{2,}\b', text)
    brands = []

    for w in words:
        # 规则：首字母大写 或 全大写
        if w[0].isupper():
            brands.append(w)

    return list(set(brands))


INVALID = ["China", "Chinese", "Brand", "Market", "Company", "Technology"]

KNOWN = ["anker", "ugreen", "miniso", "shein", "kkv", "baseus"]

def clean_brand(b):
    if any(x.lower() in b.lower() for x in INVALID):
        return False
    if b.lower() in KNOWN:
        return False
    if len(b) < 3:
        return False
    return True


# ------------------------
# 数据源（真实网页）
# ------------------------

def fetch_36kr():
    url = "https://36kr.com/newsflashes"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    items = soup.select("a.item-title")

    for it in items[:30]:
        title = it.get_text()
        link = "https://36kr.com" + it.get("href")

        brands = extract_brands(title)

        for b in brands:
            if clean_brand(b):
                results.append({
                    "brand": b,
                    "source": title,
                    "url": link,
                    "source_type": "36Kr"
                })

    return results


def fetch_techcrunch():
    url = "https://techcrunch.com/startups/"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    items = soup.select("a.post-block__title__link")

    for it in items[:30]:
        title = it.get_text().strip()
        link = it.get("href")

        brands = extract_brands(title)

        for b in brands:
            if clean_brand(b):
                results.append({
                    "brand": b,
                    "source": title,
                    "url": link,
                    "source_type": "TechCrunch"
                })

    return results


# ------------------------
# 主逻辑
# ------------------------

if st.button("开始扫描（真实数据）"):

    with st.spinner("正在抓取真实数据..."):

        data = []
        data += fetch_36kr()
        data += fetch_techcrunch()

    # 去重（品牌+来源）
    unique = {}
    for d in data:
        key = d["brand"] + d["url"]
        unique[key] = d

    results = list(unique.values())

    st.success(f"发现 {len(results)} 条真实线索")

    # ------------------------
    # 展示（可展开 + 可点击）
    # ------------------------

    for r in results:
        with st.expander(f"{r['brand']} ｜ 来源：{r['source_type']}"):

            st.write("**来源标题：**")
            st.write(r["source"])

            st.write("**原始链接：**")
            st.markdown(f"[点击查看原文]({r['url']})")

            st.write("**说明：**")
            st.info("该品牌从真实新闻标题中提取，尚未进行商标判断")
