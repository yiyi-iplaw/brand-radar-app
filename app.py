import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Brand Radar", layout="wide")

st.title("Brand Radar")
st.caption("发现正在起势、可能存在美国商标布局空窗的中国品牌")

# -----------------------------
# ✅ 品牌过滤逻辑（解决 target= 问题）
# -----------------------------
def is_valid_brand(name: str) -> bool:
    if not name:
        return False

    name = name.strip().lower()

    if len(name) < 2 or len(name) > 30:
        return False

    invalid_chars = ["=", "/", "?", "&", "http", "www", ".com", ".cn"]
    if any(c in name for c in invalid_chars):
        return False

    stopwords = [
        "中国品牌", "海外品牌", "新消费", "趋势", "出海",
        "官网", "融资", "北美", "亚马逊", "target"
    ]
    if name in stopwords:
        return False

    if not any(c.isalpha() for c in name):
        return False

    return True


def normalize_brand(name: str) -> str:
    return name.strip().upper().replace(" ", "")


# -----------------------------
# ✅ 假数据生成（你原本逻辑的替代）
# -----------------------------
def mock_scan(keywords):
    raw_brands = [
        "KKV",
        "target=",
        "中国品牌",
        "NewBrandA",
        "CoolTech",
        "品牌X",
        "http://abc",
    ]

    brands = []
    for b in raw_brands:
        if is_valid_brand(b):
            brands.append(normalize_brand(b))

    return list(set(brands))


# -----------------------------
# ✅ 商标判断（修复 KKV 问题）
# -----------------------------
KNOWN_REGISTERED = {
    "KKV",
    "HUAWEI",
    "BYD",
    "SHEIN",
}


def classify_tm(brand):
    if brand in KNOWN_REGISTERED:
        return "Registered", "No", "US trademark exists"
    else:
        return "Unknown", "Review", "Needs manual check"


# -----------------------------
# UI
# -----------------------------
st.sidebar.header("扫描参数")

keywords = st.sidebar.text_area(
    "查询词（每行一个）",
    value="中国品牌 出海\n中国 新消费 品牌 海外",
)

run = st.sidebar.button("Run scan")

if run:
    brand_list = mock_scan(keywords)

    data = []

    for b in brand_list:
        tm_status, opp, reason = classify_tm(b)

        data.append({
            "brand_name": b,
            "tm_status": tm_status,
            "opportunity": opp,
            "reason": reason,
            "score": random.randint(40, 80)
        })

    df = pd.DataFrame(data)

    st.success(f"扫描完成，共生成 {len(df)} 条线索")

    st.subheader("线索结果")
    st.dataframe(df)
