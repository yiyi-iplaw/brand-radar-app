import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Brand Radar", layout="wide")

st.title("Brand Radar")
st.caption("自动发现可触达的中国品牌商标机会")

# ==============================
# 左侧（改成产品逻辑）
# ==============================
st.sidebar.header("扫描设置")

market = st.sidebar.selectbox(
    "目标市场",
    ["US"]
)

industry = st.sidebar.selectbox(
    "行业",
    ["全部", "消费电子", "新消费"]
)

run = st.sidebar.button("开始扫描")

# ==============================
# 模拟品牌池（后面换真实数据）
# ==============================
BRANDS = [
    "ANKER", "UGREEN", "BASEUS", "SOUNDPEATS",
    "HAYLOU", "REALME", "TRIBIT", "EDIFIER",
    "MOONDROP", "AUKEY", "ORICO", "ROCKSPACE",
    "QCY", "ZEPP", "MINISO", "SHEIN", "KKV"
]

REGISTERED = {"ANKER", "SHEIN", "MINISO", "KKV"}

# ==============================
# 核心判断（接近真实业务）
# ==============================
def analyze_brand(b):
    if b in REGISTERED:
        return {
            "status": "已注册",
            "opportunity": "无",
            "reason": "美国已有注册",
            "action": "跳过"
        }

    r = random.random()

    if r > 0.6:
        return {
            "status": "不确定",
            "opportunity": "中",
            "reason": "可能已有申请",
            "action": "人工核查"
        }
    else:
        return {
            "status": "未发现",
            "opportunity": "高",
            "reason": "疑似未布局美国商标",
            "action": "优先联系"
        }

# ==============================
# 执行
# ==============================
if run:
    selected = random.sample(BRANDS, 12)

    results = []

    for b in selected:
        res = analyze_brand(b)

        results.append({
            "品牌": b,
            "商标状态": res["status"],
            "机会等级": res["opportunity"],
            "原因": res["reason"],
            "建议动作": res["action"]
        })

    df = pd.DataFrame(results)

    st.success("扫描完成")

    # KPI（换成业务指标）
    col1, col2, col3 = st.columns(3)
    col1.metric("线索数", len(df))
    col2.metric("高机会", len(df[df["机会等级"] == "高"]))
    col3.metric("需核查", len(df[df["机会等级"] == "中"]))

    st.subheader("可触达品牌列表")
    st.dataframe(df, use_container_width=True)
