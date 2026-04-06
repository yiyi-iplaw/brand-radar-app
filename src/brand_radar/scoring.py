from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from .models import Article, Lead, ScanRequest
from .parsing import infer_industry, pick_company_and_brand
from .trademark import search_public_trademark_footprint
from .utils import within_days


def detect_signals(article: Article, accel_days: int) -> list[str]:
    text = f"{article.title} {article.summary}".lower()
    signals: list[str] = []

    growth_terms = ["融资", "发布", "上市", "爆火", "增长", "获奖", "参展", "赛事"]
    global_terms = ["出海", "海外", "英文官网", "北美", "亚马逊", "独立站", "全球", "国际", "ces"]
    outreach_terms = ["创始人", "官网", "公众号", "邮箱", "品牌"]

    for term in growth_terms:
        if term in text:
            signals.append(f"growth:{term}")
    for term in global_terms:
        if term in text:
            signals.append(f"global:{term}")
    for term in outreach_terms:
        if term in text:
            signals.append(f"outreach:{term}")
    if article.published and within_days(article.published, accel_days):
        signals.append("accel:recent")
    return signals


def _score_bucket(signals: list[str], prefix: str, base: int, cap: int) -> int:
    count = sum(1 for s in signals if s.startswith(prefix))
    return min(cap, base + count * 4)


def _window_status(total_score: int, growth: int, global_: int, accel_hit: bool) -> str:
    if total_score >= 70 and global_ >= 16 and accel_hit:
        return "A"
    if total_score >= 50 and growth >= 14:
        return "B"
    return "C"


def _lead_reason(company: str, industry: str, growth: int, global_: int, tm_note: str) -> str:
    parts = []
    if company:
        parts.append(f"{company} 出现了值得关注的公开增长信号")
    if industry:
        parts.append(f"所处行业为 {industry}")
    if global_ >= 16:
        parts.append("存在较明显出海或海外布局迹象")
    if growth >= 18:
        parts.append("近阶段品牌势能较强")
    parts.append(tm_note)
    return "，".join(parts)


def _outreach_angle(company: str, global_: int, tm_gap: int) -> str:
    if global_ >= 16 and tm_gap >= 16:
        return f"以“品牌出海前的美国商标体检”切入 {company or '该公司'}"
    if tm_gap >= 16:
        return f"以“美国核心商标是否存在空窗或被动风险”切入 {company or '该公司'}"
    return f"以“品牌出海阶段的美国权利布局优化”切入 {company or '该公司'}"


def _outreach_draft(company: str, brand: str, tm_note: str, angle: str) -> str:
    target = company or brand or "贵司"
    return (
        f"您好，\n\n"
        f"近期我们注意到 {target} 在公开市场中的品牌动作和曝光有所增加。出于职业习惯，我们顺手看了一下其美国市场相关的品牌保护情况。\n\n"
        f"目前初步看到的情况是：{tm_note}\n\n"
        f"这不代表正式法律结论，但对正在走向海外或计划进入美国市场的品牌而言，往往是一个值得尽早处理的窗口。我们通常会从品牌名称、核心类别覆盖、申请主体一致性和潜在在先障碍几个方面，快速做一次实务导向的体检。\n\n"
        f"如果方便，我们可以基于 {brand or target} 先做一版简要风险梳理，帮助您判断现在是否需要正式布局。\n\n"
        f"切入建议：{angle}\n"
    )


def build_lead_rows(articles: list[Article], req: ScanRequest) -> list[Lead]:
    grouped: dict[str, list[Article]] = defaultdict(list)

    for article in articles:
        company, brand = pick_company_and_brand(article)
        key = company or brand or article.title[:40]
        grouped[key].append(article)

    leads: list[Lead] = []
    for _, group in grouped.items():
        article0 = group[0]
        company, brand = pick_company_and_brand(article0)
        merged_text = " ".join(f"{a.title} {a.summary}" for a in group)
        industry = infer_industry(merged_text)

        signals: list[str] = []
        urls: list[str] = []
        for article in group:
            signals.extend(detect_signals(article, req.accel_days))
            if article.link:
                urls.append(article.link)

        growth_score = _score_bucket(signals, "growth:", 6, 30)
        global_score = _score_bucket(signals, "global:", 4, 25)
        outreach_score = _score_bucket(signals, "outreach:", 5, 15)
        tm_gap_score, tm_note, tm_review_needed = search_public_trademark_footprint(brand or company, req.market)
        total_score = min(100, growth_score + global_score + outreach_score + tm_gap_score)
        accel_hit = any(s == "accel:recent" for s in signals)
        window_status = _window_status(total_score, growth_score, global_score, accel_hit)
        lead_reason = _lead_reason(company, industry, growth_score, global_score, tm_note)
        outreach_angle = _outreach_angle(company, global_score, tm_gap_score)
        outreach_draft = _outreach_draft(company, brand, tm_note, outreach_angle)

        leads.append(
            Lead(
                company_name=company,
                brand_name=brand,
                industry=industry,
                total_score=total_score,
                growth_score=growth_score,
                global_score=global_score,
                tm_gap_score=tm_gap_score,
                outreach_score=outreach_score,
                window_status=window_status,
                lead_reason=lead_reason,
                outreach_angle=outreach_angle,
                tm_note=tm_note,
                tm_review_needed=1 if tm_review_needed else 0,
                signals=", ".join(sorted(set(signals))),
                source_urls="\n".join(sorted(set(urls))),
                outreach_draft=outreach_draft,
            )
        )

    leads.sort(key=lambda x: x.total_score, reverse=True)
    return leads
