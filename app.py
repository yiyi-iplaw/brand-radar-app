import streamlit as st
import pandas as pd
import random
import re

st.set_page_config(page_title="Brand Radar", layout="wide")

st.title("Brand Radar")
st.caption("发现正在起势、可能存在美国商标布局空窗的中国品牌")

# ==============================
# 1️⃣ 品牌清洗（核心质量控制）
# ==============================
def is_valid_brand(name: str) -> bool:
    if not name:
        return False

    name = name.strip()

    if len(name) < 2 or len(name) > 30:
        return False

    # 过滤明显垃圾
    invalid_patterns = [
        r"http", r"www", r"\.com", r"\.cn",
        r"=", r"/", r"\?"
    ]
    if any(re.search(p, name.lower()) for p in invalid_patterns):
        return False

    # 泛词过滤
    stopwords = [
        "中国品牌", "品牌", "出海", "新消费", "趋势",
        "官网", "海外", "融资", "北美", "亚马逊"
    ]
    if name in stopwords:
        return False

    # 必须包含字母
    if not any(c.isalpha() for c in name):
        return False

    return True


def normalize_brand(name: str) -> str:
    return name.strip().upper().replace(" ", "")


# ==============================
# 2️⃣ 模拟真实品牌池（替代垃圾mock）
# ==============================
REALISTIC_BRANDS = [
    "KKV",
    "POP MART",
    "MINISO",
    "SHEIN",
    "ANKER",
    "UGREEN",
    "BASEUS",
    "SOUNDPEATS",
    "HAYLOU",
    "REALME",
    "ZEPP",
    "XIAOMI",
    "ROCKSPACE",
    "ORICO",
    "AUKEY",
    "BLITZWOLF",
    "QCY",
    "TRIBIT",
    "EDIFIER",
    "MOONDROP"
]


def mock_scan(keywords: str, max_results: int):
    selected = random.sample(REALISTIC_BRANDS, min(max_results, len(REALISTIC_BRANDS)))

    cleaned = []
    for b in selected:
        if is_valid_brand(b):
            cleaned.append(normalize_brand(b))

    return cleaned


# ==============================
# 3️⃣ 商标判断（当前版本：规则 + 占位）
# ==============================
KNOWN_REGISTERED = {
    "KKV",
    "ANKER",
    "SHEIN",
    "MINISO",
    "XIAOMI"
}


def classify_tm(brand: str):
    """
    下一步这里可以直接接 USPTO API
    """
    if brand in KNOWN_REGISTERED:
        return "Registered", "No", "US trademark exists"

    # 模拟判断逻辑
    score = random.random()

    if score > 0.7:
        return "Likely Registered", "Low", "Possible existing filings"
    elif score > 0.4:
        return "Unknown", "Review", "Needs manual check"
    else:
        return "No Record", "High", "Potential trademark gap"


# ==============================
# 4️⃣ 评分模型（更接近真实产品）
# ==============================
def score_brand():
    growth = random.randint(5, 20)
    global_score = random.randint(5, 25)
    tm_gap = random.randint(5, 25)
    outreach = random.randint(5, 10)

    total = growth + global_score + tm_gap + outreach

    return total, growth, global_score, tm_gap, outreach


# ==============================
# UI
# ==============================
st.sidebar.header("扫描参数")

keywords = st.sidebar.text_area(
    "查询词（每行一个）",
    value="中国品牌 出海\n中国 新消费 品牌 海外",
)

max_results = st.sidebar.slider("抓取品牌数量", 5, 30, 15)

run = st.sidebar.button("Run scan")

# ==============================
# 执行
# ==============================
if run:
    brand_list = mock_scan(keywords, max_results)

    data = []

    for b in brand_list:
        tm_status, opp, reason = classify_tm(b)
        total, growth, global_score, tm_gap, outreach = score_brand()

        data.append({
            "brand_name": b,
            "total_score": total,
            "growth_score": growth,
            "global_score": global_score,
            "tm_gap_score": tm_gap,
            "outreach_score": outreach,
            "tm_status": tm_status,
            "opportunity": opp,
            "reason": reason
        })

    df = pd.DataFrame(data).sort_values(by="total_score", ascending=False)

    st.success(f"扫描完成，共生成 {len(df)} 条线索")

    # KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("Leads", len(df))
    col2.metric("Avg Score", round(df["total_score"].mean(), 1))
    col3.metric("High Opportunity", len(df[df["opportunity"] == "High"]))

    st.subheader("线索结果")
    st.dataframe(df, use_container_width=True)
