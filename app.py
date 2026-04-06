import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote

st.set_page_config(page_title="Brand Radar", layout="wide")

st.title("Brand Radar")
st.caption("基于可验证来源的美国商标机会筛选工具")

# ---------------------------
# Sidebar（去掉你不喜欢的输入逻辑）
# ---------------------------

st.sidebar.header("扫描设置")

market = st.sidebar.selectbox("目标市场", ["US"], index=0)

industry = st.sidebar.selectbox("行业", ["消费电子", "家居", "新能源", "全部"], index=0)

run = st.sidebar.button("开始扫描")

# ---------------------------
# 数据源（真实品牌池，可替换）
# ---------------------------

BRAND_POOL = [
    "ANKER", "UGREEN", "BASEUS", "MINISO", "KKV",
    "SHEIN", "REALME", "EDIFIER", "SOUNDPEATS",
    "TRIBIT", "ORICO", "AUKEY", "ROCKSPACE"
]

# ---------------------------
# USPTO 查询（真实 authority）
# ---------------------------

def search_uspto(brand):
    try:
        url = f"https://developer.uspto.gov/ibd-api/v1/application/publications?searchText={quote(brand)}&rows=5"
        r = requests.get(url, timeout=5)

        if r.status_code != 200:
            return "Unknown", []

        data = r.json()

        results = data.get("results", [])

        evidence = []

        if not results:
            return "未发现", []

        for item in results[:3]:
            serial = item.get("serialNumber", "")
            mark = item.get("markIdentification", "")

            if serial:
                tsdr = f"https://tsdr.uspto.gov/#caseNumber={serial}&caseType=SERIAL_NO"
                evidence.append({
                    "title": f"{mark} ({serial})",
                    "url": tsdr
                })

        return "已发现记录", evidence

    except:
        return "Unknown", []

# ---------------------------
# 判断逻辑（全部基于 evidence）
# ---------------------------

def analyze_brand(brand):
    status, evidence = search_uspto(brand)

    if status == "未发现":
        return {
            "品牌": brand,
            "商标状态": "未发现",
            "机会等级": "高",
            "原因": "USPTO未检索到记录",
            "evidence": []
        }

    elif status == "已发现记录":
        return {
            "品牌": brand,
            "商标状态": "已存在记录",
            "机会等级": "低",
            "原因": "USPTO存在注册或申请",
            "evidence": evidence
        }

    else:
        return {
            "品牌": brand,
            "商标状态": "不确定",
            "机会等级": "中",
            "原因": "查询异常或数据不足",
            "evidence": []
        }

# ---------------------------
# 主逻辑
# ---------------------------

if run:

    results = []

    for b in BRAND_POOL:
        res = analyze_brand(b)
        results.append(res)

    df = pd.DataFrame(results)

    st.success(f"扫描完成，共生成 {len(df)} 条线索")

    # KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("总线索", len(df))
    col2.metric("高机会", len(df[df["机会等级"] == "高"]))
    col3.metric("需人工核查", len(df[df["商标状态"] == "不确定"]))

    st.subheader("可触达品牌列表（可展开查看证据）")

    for i, row in df.iterrows():
        with st.expander(f"{row['品牌']} ｜ {row['机会等级']}机会"):

            st.write(f"**商标状态**：{row['商标状态']}")
            st.write(f"**判断原因**：{row['原因']}")

            st.write("**权威来源（USPTO）**")

            if row["evidence"]:
                for ev in row["evidence"]:
                    st.markdown(f"- [{ev['title']}]({ev['url']})")
            else:
                st.warning("未检索到记录（建议人工确认）")
