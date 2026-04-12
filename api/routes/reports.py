"""
Reports routes — store and retrieve deep dive reports.
Reports are saved as JSON files in data/reports/.
"""

import os
import json
import glob
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import DATA_DIR

REPORTS_DIR = os.path.join(DATA_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

router = APIRouter(prefix="/api/reports", tags=["reports"])


class SaveReportRequest(BaseModel):
    ticker: str
    report_html: str
    summary: dict  # { verdict, score, rank, price, date }


def _report_filename(ticker: str, timestamp: str) -> str:
    """NKT_2026-04-12T13-00-00.json"""
    safe_ts = timestamp.replace(":", "-")
    return f"{ticker}_{safe_ts}.json"


@router.get("/")
def list_reports() -> list[dict]:
    """List all saved reports, newest first."""
    reports = []
    for filepath in glob.glob(os.path.join(REPORTS_DIR, "*.json")):
        try:
            with open(filepath) as f:
                data = json.load(f)
            reports.append({
                "id": os.path.basename(filepath).replace(".json", ""),
                "ticker": data["ticker"],
                "date": data["date"],
                "summary": data.get("summary", {}),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    reports.sort(key=lambda r: r["date"], reverse=True)
    return reports


@router.get("/{report_id}")
def get_report(report_id: str) -> dict:
    """Get a single report by ID."""
    filepath = os.path.join(REPORTS_DIR, f"{report_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")

    with open(filepath) as f:
        return json.load(f)


@router.post("/")
def save_report(req: SaveReportRequest) -> dict:
    """Save a new deep dive report."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%dT%H-%M-%S")

    report = {
        "ticker": req.ticker.upper(),
        "date": now.isoformat(),
        "summary": req.summary,
        "report_html": req.report_html,
    }

    filename = _report_filename(req.ticker.upper(), date_str)
    filepath = os.path.join(REPORTS_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)

    return {
        "id": filename.replace(".json", ""),
        "ticker": report["ticker"],
        "date": report["date"],
    }


@router.delete("/{report_id}")
def delete_report(report_id: str) -> dict:
    """Delete a report."""
    filepath = os.path.join(REPORTS_DIR, f"{report_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")
    os.remove(filepath)
    return {"deleted": report_id}


@router.get("/skill/info")
def get_skill_info() -> dict:
    """Return the deep-dive skill content and last modified date."""
    # __file__ = api/routes/reports.py → go up 3 levels to repo root
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    skill_paths = [
        os.path.join(repo_root, ".claude", "skills", "deep-dive.md"),
    ]

    for skill_path in skill_paths:
        if os.path.exists(skill_path):
            mtime = os.path.getmtime(skill_path)
            modified = datetime.fromtimestamp(mtime).isoformat()

            with open(skill_path) as f:
                raw = f.read()

            # Strip frontmatter
            content = raw
            if raw.startswith("---"):
                parts = raw.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2].strip()

            return {
                "name": "deep-dive",
                "description": "Run a deep investment analysis on a stock candidate from the screener",
                "last_modified": modified,
                "content": content,
            }

    raise HTTPException(status_code=404, detail="Skill file not found")
