from __future__ import annotations

import re
from collections import Counter

from .models import Article
from .utils import normalize_space

INDUSTRY_KEYWORDS = {
    "新能源": ["新能源", "电动车", "电池", "充电", "汽车", "两轮电动", "e-bike", "ev"],
    "骑行/机车": ["骑行", "机车", "摩托", "自行车", "头盔", "赛事", "赛道"],
    "智能硬件": ["智能硬件", "耳机", "机器人", "穿戴", "硬件", "ai 硬件", "传感器"],
    "户外": ["露营", "户外", "运动", "徒步", "滑雪", "越野"],
    "家居/工具": ["家居", "工具", "收纳", "清洁", "小家电"],
    "个护/美容": ["美容", "个护", "护理", "按摩", "护肤"],
}

COMPANY_SUFFIXES = [
    "公司",
    "集团",
    "科技",
    "实业",
    "股份",
    "有限公司",
    "有限责任公司",
    "品牌",
    "车业",
]


def infer_industry(text: str) -> str:
    text_l = text.lower()
    scores = {}
    for industry, words in INDUSTRY_KEYWORDS.items():
        scores[industry] = sum(1 for w in words if w.lower() in text_l)
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else "其他"


def extract_candidates(text: str) -> list[str]:
    text = normalize_space(text)
    candidates: list[str] = []

    quoted = re.findall(r"[“\"]([^”\"]{2,24})[”\"]", text)
    candidates.extend(quoted)

    cn_names = re.findall(r"([\u4e00-\u9fffA-Za-z0-9·]{2,30}(?:" + "|".join(COMPANY_SUFFIXES) + r"))", text)
    candidates.extend(cn_names)

    latin = re.findall(r"\b[A-Z][A-Za-z0-9\-]{2,20}\b", text)
    candidates.extend(latin)

    cleaned = []
    for item in candidates:
        item = normalize_space(item)
        if len(item) < 2:
            continue
        if item.lower() in {"china", "amazon", "google", "tesla"}:
            continue
        cleaned.append(item)
    return cleaned


def pick_company_and_brand(article: Article) -> tuple[str, str]:
    text = f"{article.title} {article.summary}"
    candidates = extract_candidates(text)
    if not candidates:
        return "", ""

    counts = Counter(candidates)
    ranked = [name for name, _ in counts.most_common()]

    company = ""
    brand = ""
    for name in ranked:
        if any(suffix in name for suffix in COMPANY_SUFFIXES):
            company = name
            break
    if not company:
        company = ranked[0]

    for name in ranked:
        if name != company:
            brand = name
            break
    if not brand:
        brand = company

    return company, brand
