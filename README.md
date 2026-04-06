# Brand Radar

A GitHub-hostable Streamlit MVP for finding early-stage Chinese brands with U.S. trademark opportunity signals.

## What it does

- Pulls recent public news and announcement signals from Google News RSS
- Extracts likely company and brand names with practical heuristics
- Scores each lead across:
  - Growth momentum
  - Globalization / going-global intent
  - Trademark opportunity gap
  - Outreach readiness
- Stores leads in SQLite
- Lets you review, edit, export, and prioritize outreach

## What it does **not** do

This is a lead-generation and signal-ranking tool. It is **not** a legal clearance opinion, a full knockout search, or a substitute for attorney review.

The trademark module uses public web-footprint heuristics by default, because that makes the app runnable without paid APIs. You can later swap in an official USPTO / commercial search connector.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Optional environment variables

Create a `.env` or export values in your shell:

```bash
export BRAND_RADAR_DB_PATH=brand_radar.db
export BRAND_RADAR_DEFAULT_MARKETS=us
export BRAND_RADAR_REQUEST_TIMEOUT=15
```

## How to use

1. Open the app.
2. Enter industries, queries, and time windows.
3. Click **Run scan**.
4. Review top-scoring leads.
5. Open a lead to see source articles, detected signals, and outreach draft.
6. Export selected leads to CSV.

## Suggested queries

Use queries like:

- 中国品牌 出海 融资
- 中国 新消费 品牌 海外
- 中国 骑行 品牌 北美
- 中国 智能硬件 英文官网
- 中国 新能源 参展 海外
- 张雪机车 类似 品牌 赛事 海外

## Project structure

```text
brand-radar/
├─ app.py
├─ requirements.txt
├─ README.md
├─ src/brand_radar/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ db.py
│  ├─ feeds.py
│  ├─ models.py
│  ├─ parsing.py
│  ├─ scoring.py
│  ├─ trademark.py
│  └─ utils.py
└─ .github/workflows/python.yml
```

## GitHub deployment notes

This repo is ready to push to GitHub.

Example:

```bash
git init
git add .
git commit -m "Initial commit: Brand Radar MVP"
git branch -M main
git remote add origin YOUR_REPO_URL
git push -u origin main
```

For Streamlit Community Cloud, set the main file to `app.py`.

## Next upgrades I recommend

- Replace heuristic trademark lookup with an official or commercial U.S. trademark connector
- Add TMview / WIPO / domain checks
- Add company website crawler depth control
- Add CRM status and email tracking
- Add LLM-based entity normalization
- Add custom source packs for specific industries
