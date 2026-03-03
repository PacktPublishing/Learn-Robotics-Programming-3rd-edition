from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


ROBOT_CONTROL_DIR = Path("/app/robot_control")
ENV_PATH = ROBOT_CONTROL_DIR / ".env.json"


def _load_template_context() -> dict:
    if not ENV_PATH.exists():
        return {}
    with ENV_PATH.open() as env_file:
        return json.load(env_file)


app = FastAPI(title="robot-control-web")
templates = Jinja2Templates(directory="/app")
templates.env.auto_reload = True
templates.env.cache = {}

app.mount("/libs", StaticFiles(directory="/opt/web-libs"), name="libs")


@app.get("/")
async def root(request: Request):
    context = {"request": request, **_load_template_context()}
    return templates.TemplateResponse("robot_control/index.html", context)


@app.get("/{path:path}")
async def robot_control_page(path: str, request: Request):
    target = (ROBOT_CONTROL_DIR / path).resolve()
    if not target.is_file() or ROBOT_CONTROL_DIR.resolve() not in target.parents:
        raise HTTPException(status_code=404, detail="Not found")

    if target.suffix in {".html", ".j2"}:
        context = {"request": request, **_load_template_context()}
        return templates.TemplateResponse(f"robot_control/{path}", context)

    return FileResponse(target)