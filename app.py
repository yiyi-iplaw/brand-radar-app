import re
import time
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(page_title="Brand Radar", layout="wide")

# =========================
# 基础配置
# =========================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
}

SOURCE_WEIGHTS = {
    "垂直论坛": 40,
    "小红书": 30,
    "抖音": 20,
}

SOURCE_DOMAINS = {
    "小红书": ["xiaohongshu.com"],
    "抖音": ["douyin.com"],
}

INDUSTRY_CONFIG = {
    "摩托车/机车": {
        "keywords": ["摩托", "机车", "骑行", "仿赛", "巡航", "改装", "试驾", "测评"],
        "forum_terms": ["论坛", "车友", "摩托吧", "机车论坛", "骑行论坛"],
    },
    "音频/耳机": {
        "keywords": ["耳机", "音频", "HiFi", "音响", "播放器", "塞子", "头戴"],
        "forum_terms": ["论坛", "烧友", "耳机论坛", "发烧友", "head-fi"],
    },
    "户外/露营": {
        "keywords": ["露营", "户外", "徒步", "冲锋衣", "天幕", "帐篷", "炊具"],
        "forum_terms": ["论坛", "户外论坛", "露营论坛", "装备论坛"],
    },
    "骑行/自行车": {
        "keywords": ["自行车", "公路车", "山地车", "骑行", "轮组", "头盔", "车架"],
        "forum_terms": ["论坛", "骑行论坛", "车友论坛"],
    },
    "咖啡/家电": {
        "keywords": ["咖啡机", "磨豆机", "手冲", "胶囊机", "家电", "小家电"],
        "forum_terms": ["论坛", "咖啡论坛", "家电论坛"],
    },
    "宠物": {
        "keywords": ["宠物", "猫砂盆", "喂食器", "饮水机", "猫粮", "狗粮"],
        "forum_terms": ["论坛", "宠物论坛", "养宠论坛"],
    },
}

GENERIC_BLACKLIST = {
    "品牌", "中国", "国产", "用户", "推荐", "测评", "评测", "论坛", "体验", "开箱",
    "视频", "合集", "店铺", "旗舰店", "官方", "产品", "公司", "市场", "海外",
    "抖音", "小红书", "知乎", "微博", "头盔", "耳机", "机车", "摩托", "露营",
    "自行车", "咖啡机", "家电", "宠物", "猫", "狗", "新款", "系列", "网友",
    "老师", "测", "真的", "一个", "这个", "那个", "什么", "如何", "值得", "入手",
    "anthropic", "spacex", "tesla", "apple", "xiaomi", "huawei", "byd", "anker",
    "ugreen", "shein", "miniso", "popmart", "openai", "chatgpt", "google", "meta",
}

TRIGGER_WORDS = [
    "测评", "评测", "推荐", "开箱", "试驾", "实测", "改装", "入手", "体验", "对比",
    "发布", "上市", "首发", "车友", "讨论", "爆火", "口碑", "圈内", "玩家", "烧友",
]

POSITIVE_SIGNALS = [
    "测评", "评测", "推荐", "开箱", "试驾", "实测", "改装", "口碑", "车友", "玩家",
    "烧友", "讨论", "对比", "入手", "体验", "值得", "首发", "发布", "上市", "爆火",
]

# =========================
# Sidebar
# =========================
st.sidebar.header("扫描设置")

selected_industries = st.sidebar.multiselect(
    "关注行业",
    list(INDUSTRY_CONFIG.keys()),
    default=["摩托车/机车", "音频/耳机"]
)

lookback_days = st.sidebar.select_slider(
    "观察窗口",
    options=[30, 90, 180],
    value=180
)

selected_sources = st.sidebar.multiselect(
    "数据源",
    ["垂直论坛", "小红书", "抖音"],
    default=["垂直论坛", "小红书", "抖音"]
)

min_evidence = st.sidebar.slider(
    "最少证据条数",
    min_value=2,
    max_value=8,
    value=3
)

max_search_results_per_query = st.sidebar.slider(
    "每个查询抓取条数",
    min_value=10,
    max_value=50,
    value=20,
    step=5
)

run = st.sidebar.button("开始扫描")

# =========================
# 工具函数
# =========================
def domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def classify_source(url: str, title: str, snippet: str) -> str:
    domain = domain_of(url)
    text = f"{title} {snippet}".lower()

    for label, domains in SOURCE_DOMAINS.items():
        if any(d in domain for d in domains):
            return label

    if "forum" in domain or "bbs" in domain or "club" in domain or "tieba" in domain:
        return "垂直论坛"

    if "论坛" in text or "车友" in text or "烧友" in text or "玩家" in text:
        return "垂直论坛"

    return "其他"

def normalize_candidate(name: str) -> str:
    name = name.strip("《》[]【】()（）:：,，.。!！?？'\" ").strip()
    name = re.sub(r"\s+", "", name)
    return name

def parse_date_from_text(text: str):
    # 兼容几种常见形式
    patterns = [
        r"(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})",
        r"(20\d{2})\.(\d{1,2})\.(\d{1,2})",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            try:
                y, mth, d = map(int, m.groups())
                return datetime(y, mth, d)
            except Exception:
                pass

    rel = re.search(r"(\d+)\s*(天前|日前)", text)
    if rel:
        days = int(rel.group(1))
        return datetime.now() - timedelta(days=days)

    rel_month = re.search(r"(\d+)\s*(个月前)", text)
    if rel_month:
        months = int(rel_month.group(1))
        return datetime.now() - timedelta(days=months * 30)

    return None

def build_queries(industry_name: str, source_name: str, lookback_days: int):
    cfg = INDUSTRY_CONFIG[industry_name]
    kw = cfg["keywords"][:3]
    forum_terms = cfg["forum_terms"][:2]

    time_hint = {
        30: "近一个月",
        90: "近三个月",
        180: "近半年",
    }[lookback_days]

    queries = []

    if source_name == "小红书":
        for k in kw:
            queries.append(f"site:xiaohongshu.com {k} 品牌 测评 {time_hint}")
            queries.append(f"site:xiaohongshu.com {k} 推荐 国产 {time_hint}")

    elif source_name == "抖音":
        for k in kw:
            queries.append(f"site:douyin.com {k} 品牌 开箱 {time_hint}")
            queries.append(f"site:douyin.com {k} 评测 推荐 {time_hint}")

    elif source_name == "垂直论坛":
        for k in kw:
            for ft in forum_terms:
                queries.append(f"{k} {ft} 国产 品牌 测评 {time_hint}")
                queries.append(f"{k} {ft} 推荐 对比 {time_hint}")

    return queries[:6]

def ddg_search(query: str, max_results: int = 20):
    # DuckDuckGo HTML 结果页，避免 JS
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    try:
        resp = requests.post(url, data=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for block in soup.select(".result"):
        a = block.select_one(".result__title a")
        snippet_el = block.select_one(".result__snippet")
        if not a:
            continue

        title = a.get_text(" ", strip=True)
        href = a.get("href", "").strip()
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        if not href or href.startswith("/y.js"):
            continue

        results.append({
            "title": title,
            "url": href,
            "snippet": snippet,
        })

        if len(results) >= max_results:
            break

    return results

def extract_brand_candidates(text: str):
    candidates = set()
    clean_text = re.sub(r"\s+", " ", text)

    # 英文/数字品牌
    for token in re.findall(r"\b[A-Z][A-Za-z0-9\-]{2,20}\b", clean_text):
        token_n = normalize_candidate(token)
        if token_n and token_n.lower() not in GENERIC_BLACKLIST and len(token_n) >= 3:
            candidates.add(token_n)

    # 中文候选：触发词前后抓
    patterns = [
        r"([一-龥A-Za-z0-9·]{2,12})(?:测评|评测|推荐|开箱|试驾|实测|改装|体验|对比)",
        r"(?:测评|评测|推荐|开箱|试驾|实测|改装|体验|对比)([一-龥A-Za-z0-9·]{2,12})",
        r"([一-龥A-Za-z0-9·]{2,12})(?:品牌|机车|耳机|音响|露营|帐篷|自行车|咖啡机|宠物)",
        r"(?:来自|国产|国货|新锐|小众)([一-龥A-Za-z0-9·]{2,12})",
        r"([一-龥A-Za-z0-9·]{2,12})(?:车友|玩家|烧友)",
    ]

    for p in patterns:
        for m in re.findall(p, clean_text):
            token_n = normalize_candidate(m)
            if not token_n:
                continue
            low = token_n.lower()
            if low in GENERIC_BLACKLIST:
                continue
            if len(token_n) < 2 or len(token_n) > 12:
                continue
            # 过滤纯泛词
            if token_n in GENERIC_BLACKLIST:
                continue
            candidates.add(token_n)

    return list(candidates)

def evidence_signal_score(title: str, snippet: str, source_type: str):
    text = f"{title} {snippet}"
    score = SOURCE_WEIGHTS.get(source_type, 10)
    hits = sum(1 for w in POSITIVE_SIGNALS if w in text)
    score += min(hits * 5, 20)
    return score

def dedupe_evidence(items):
    seen = set()
    output = []
    for it in items:
        key = it["url"]
        if key not in seen:
            seen.add(key)
            output.append(it)
    return output

def compute_brand_scores(items):
    source_types = {i["source_type"] for i in items}
    source_count = len(items)

    # 圈层强度：论坛权重大
    niche_strength = min(sum(SOURCE_WEIGHTS.get(i["source_type"], 0) for i in items), 100)

    # 来源分散度
    diversity_score = 0
    if "垂直论坛" in source_types:
        diversity_score += 30
    if "小红书" in source_types:
        diversity_score += 20
    if "抖音" in source_types:
        diversity_score += 15
    diversity_score = min(diversity_score, 40)

    # 持续性：优先看时间跨度；没有时间时，看来源分散 + 证据条数
    dates = sorted([i["parsed_date"] for i in items if i["parsed_date"] is not None])
    persistence_score = 0
    persistence_reason = []

    if len(dates) >= 2:
        span_days = (dates[-1] - dates[0]).days
        if span_days >= 120:
            persistence_score = 30
            persistence_reason.append(f"可见时间跨度约 {span_days} 天")
        elif span_days >= 60:
            persistence_score = 22
            persistence_reason.append(f"可见时间跨度约 {span_days} 天")
        elif span_days >= 30:
            persistence_score = 15
            persistence_reason.append(f"可见时间跨度约 {span_days} 天")
        else:
            persistence_score = 8
            persistence_reason.append(f"时间跨度较短，约 {span_days} 天")
    else:
        if len(source_types) >= 2 and source_count >= 4:
            persistence_score = 14
            persistence_reason.append("虽无足够日期，但来源分散且证据条数较多")
        elif source_count >= 3:
            persistence_score = 8
            persistence_reason.append("证据条数达到基础阈值，但持续性证据有限")

    # 可靠度：来源类型 + 条数 + 是否有论坛
    reliability = 0
    if "垂直论坛" in source_types:
        reliability += 40
    reliability += min(source_count * 10, 30)
    reliability += min(len(source_types) * 10, 30)
    reliability = min(reliability, 100)

    # 总分
    total = round(
        niche_strength * 0.35
        + diversity_score * 0.20
        + persistence_score * 0.25
        + reliability * 0.20
    )

    return {
        "总分": total,
        "圈层强度": min(round(niche_strength), 100),
        "来源分散度": min(round(diversity_score), 100),
        "持续性": min(round(persistence_score), 100),
        "可靠度": min(round(reliability), 100),
        "持续性说明": "；".join(persistence_reason) if persistence_reason else "持续性证据有限",
    }

def recommendation_from_scores(score_dict, items):
    total = score_dict["总分"]
    source_types = {i["source_type"] for i in items}
    forum_count = sum(1 for i in items if i["source_type"] == "垂直论坛")

    if total >= 80 and forum_count >= 2:
        return "高优先级：建议立即人工商标预检并建立跟进名单"
    if total >= 65:
        return "中高优先级：建议人工快速复核品牌主体与商标基础状态"
    if total >= 50:
        return "观察名单：有一定圈层信号，但还不够强"
    return "低优先级：暂不建议投入时间"

def confidence_label(score_dict):
    r = score_dict["可靠度"]
    if r >= 80:
        return "高"
    if r >= 60:
        return "中"
    return "低"

# =========================
# 扫描主流程
# =========================
@st.cache_data(show_spinner=False, ttl=3600)
def run_scan(industry_list, source_list, lookback_days, max_per_query):
    brand_map = defaultdict(list)

    all_queries = []
    for ind in industry_list:
        for src in source_list:
            all_queries.extend(build_queries(ind, src, lookback_days))

    # 去重查询
    all_queries = list(dict.fromkeys(all_queries))

    for q in all_queries:
        results = ddg_search(q, max_results=max_per_query)
        time.sleep(0.8)

        for res in results:
            source_type = classify_source(res["url"], res["title"], res["snippet"])
            if source_type not in source_list:
                continue

            text_blob = f"{res['title']} {res['snippet']}"
            candidates = extract_brand_candidates(text_blob)
            parsed_date = parse_date_from_text(text_blob)

            for c in candidates:
                low = c.lower()
                if low in GENERIC_BLACKLIST:
                    continue
                if len(c) < 2 or len(c) > 12:
                    continue

                evidence = {
                    "title": res["title"],
                    "url": res["url"],
                    "snippet": res["snippet"],
                    "source_type": source_type,
                    "parsed_date": parsed_date,
                    "query": q,
                    "signal_score": evidence_signal_score(res["title"], res["snippet"], source_type),
                }
                brand_map[c].append(evidence)

    # 清洗、聚合、过滤
    leads = []
    for brand, items in brand_map.items():
        items = dedupe_evidence(items)

        # 核心过滤：至少达到最少证据阈值，且必须包含论坛或至少两类来源
        source_types = {i["source_type"] for i in items}
        if len(items) < min_evidence:
            continue
        if "垂直论坛" not in source_types and len(source_types) < 2:
            continue

        score_dict = compute_brand_scores(items)
        recommendation = recommendation_from_scores(score_dict, items)

        # 判断逻辑
        rationale = []
        rationale.append(f"共发现 {len(items)} 条证据")
        rationale.append(f"覆盖来源：{'、'.join(sorted(source_types))}")
        if "垂直论坛" in source_types:
            rationale.append("存在垂直论坛讨论，圈层认可度较强")
        rationale.append(score_dict["持续性说明"])

        leads.append({
            "brand": brand,
            "scores": score_dict,
            "recommendation": recommendation,
            "confidence": confidence_label(score_dict),
            "rationale": rationale,
            "evidence": sorted(items, key=lambda x: (x["parsed_date"] or datetime(2000,1,1)), reverse=True),
        })

    leads.sort(key=lambda x: (x["scores"]["总分"], len(x["evidence"])), reverse=True)
    return leads, all_queries

# =========================
# UI
# =========================
st.title("Brand Radar")
st.caption("面向中国早期品牌的圈层信号扫描器")

if not selected_industries:
    st.warning("先在左侧至少选择一个行业。")
elif not selected_sources:
    st.warning("先在左侧至少选择一个数据源。")
else:
    if run:
        with st.spinner("正在扫描真实页面并聚合品牌..."):
            leads, used_queries = run_scan(
                selected_industries,
                selected_sources,
                lookback_days,
                max_search_results_per_query
            )

        top_col1, top_col2, top_col3 = st.columns(3)
        top_col1.metric("候选品牌", len(leads))
        top_col2.metric("观察窗口", f"{lookback_days} 天")
        top_col3.metric("最少证据阈值", min_evidence)

        with st.expander("本次检索策略", expanded=False):
            st.write("使用的查询：")
            for q in used_queries:
                st.code(q)

        if not leads:
            st.error("本次没有发现达到阈值的候选品牌。你可以放宽行业、降低最少证据条数，或提高每个查询抓取条数。")
        else:
            for lead in leads:
                s = lead["scores"]
                header = f"{lead['brand']} ｜ 总分 {s['总分']} ｜ 可靠度 {lead['confidence']}"
                with st.expander(header, expanded=False):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("圈层强度", s["圈层强度"])
                    c2.metric("来源分散度", s["来源分散度"])
                    c3.metric("持续性", s["持续性"])
                    c4.metric("可靠度", s["可靠度"])

                    st.write("### 推荐结论")
                    st.write(lead["recommendation"])

                    st.write("### 判断逻辑")
                    for r in lead["rationale"]:
                        st.write(f"- {r}")

                    st.write("### 证据列表")
                    for ev in lead["evidence"]:
                        date_text = ev["parsed_date"].strftime("%Y-%m-%d") if ev["parsed_date"] else "未识别日期"
                        st.markdown(f"**[{ev['title']}]({ev['url']})**")
                        st.write(f"来源：{ev['source_type']}｜日期：{date_text}")
                        if ev["snippet"]:
                            st.caption(ev["snippet"])
                        st.divider()
    else:
        st.info("先在左侧设置参数，再点击“开始扫描”。")
