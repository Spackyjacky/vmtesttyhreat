#!/usr/bin/env python3
"""Local-LAN web dashboard for searching captured vehicle events.

Run with: uvicorn dashboard.app:app --host 0.0.0.0 --port 8080
(from the reolink-anpr/ directory, so relative imports resolve).

Binds to the Pi's LAN interface only — this is not designed or intended to
be exposed to the internet.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import db
from config import load_config

config = load_config()
storage = config["storage"]
DB_PATH = storage["database_path"]
CAPTURES_DIR = Path(storage["captures_dir"])

db.init_db(DB_PATH)

app = FastAPI(title="Reolink ANPR Dashboard")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/captures", StaticFiles(directory=str(CAPTURES_DIR)), name="captures")


def _event_to_dict(event: db.Event) -> dict:
    return {
        "id": event.id,
        "timestamp": event.timestamp,
        "camera": event.camera,
        "vehicle_type": event.vehicle_type,
        "plate": event.plate,
        "plate_confidence": event.plate_confidence,
        "color": event.color,
        "full_image_url": f"/captures/{event.full_image_path}",
        "vehicle_image_url": f"/captures/{event.vehicle_image_path}",
        "plate_image_url": f"/captures/{event.plate_image_path}" if event.plate_image_path else None,
    }


@app.get("/api/search")
def api_search(
    plate: str | None = None,
    color: str | None = None,
    camera: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 200,
    offset: int = 0,
):
    events = db.search_events(
        DB_PATH,
        plate=plate or None,
        color=color or None,
        camera=camera or None,
        start=start or None,
        end=end or None,
        limit=min(limit, 500),
        offset=offset,
    )
    return JSONResponse([_event_to_dict(e) for e in events])


@app.get("/")
def search_page(
    request: Request,
    plate: str | None = None,
    color: str | None = None,
    camera: str | None = None,
    start: str | None = None,
    end: str | None = None,
):
    events = db.search_events(
        DB_PATH,
        plate=plate or None,
        color=color or None,
        camera=camera or None,
        start=start or None,
        end=end or None,
        limit=200,
    )
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "events": events,
            "colors": db.distinct_colors(DB_PATH),
            "cameras": db.distinct_cameras(DB_PATH),
            "filters": {
                "plate": plate or "",
                "color": color or "",
                "camera": camera or "",
                "start": start or "",
                "end": end or "",
            },
        },
    )


@app.get("/event/{event_id}")
def event_detail(request: Request, event_id: int):
    event = db.get_event(DB_PATH, event_id)
    if event is None:
        return templates.TemplateResponse(
            "not_found.html", {"request": request, "event_id": event_id}, status_code=404
        )
    return templates.TemplateResponse("event.html", {"request": request, "event": event})
