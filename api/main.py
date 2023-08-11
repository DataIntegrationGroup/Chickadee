# ===============================================================================
# Copyright 2023 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import json
import os
from datetime import datetime

import jsbeautifier
from fastapi import Depends
from numpy import array, flipud, fliplr
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from app import app
from constants import API_PREFIX
from pathlib import Path

if int(os.environ.get("CHICKADEE_ERASE_AND_REBUILD_DB", 0)):
    from database import engine
    from models import sample, project, analysis, Base

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

from routes import sample, project, analysis, material, process

app.include_router(sample.router)
app.include_router(project.router)
app.include_router(analysis.router)
app.include_router(material.router)
app.include_router(process.router)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))


@app.get("/mapboxtoken")
def mapboxtoken():
    return {
        "token": "pk.eyJ1IjoiamFrZXJvc3N3ZGkiLCJhIjoiY2s3M3ZneGl4MGhkMDNrcjlocmNuNWg4bCJ9.4r1DRDQ_ja0fV2nnmlVT0A"
    }


@app.get("/source_sink", response_class=HTMLResponse)
def source_sink(request: Request, age: str = None, kca: str = None):
    match = None
    graphjson = None
    graphjson_decision_function = None

    if age and kca:
        from routes.process import source_matcher

        match = source_matcher(age, kca)
    else:
        age = "Age"
        kca = "K/Ca"

    if match:
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.layout.margin = {"l": 80, "r": 85, "t": 70, "b": 0}

        fig.layout.xaxis.title = "Age (Ma)"
        fig.layout.yaxis.title = "K/Ca"
        fig.layout.title = {
            "text": "Probability Density",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }

        sxs = match["source"].pop("ages")
        sys = match["source"].pop("kcas")

        xs = match.pop("ages")
        ys = match.pop("kcas")
        full_probability = match.pop("full_probability")
        decision_function = match.pop("decision_function")
        pxs = match.pop("pxs")
        pys = match.pop("pys")

        bxs = match["mean_closest"].pop("ages")
        bys = match["mean_closest"].pop("kcas")
        # bxs = match.pop("mean_closest_xs")
        # bys = match.pop("mean_closest_ys")

        nage = match["sink"]["age"]
        nkca = match["sink"]["kca"]
        # nage, _ = age.split(",")
        # nkca, _ = kca.split(",")

        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name="TestPlot"))
        fig.add_trace(go.Scatter(x=bxs, y=bys, mode="markers", name="Background"))
        fig.add_trace(
            go.Scatter(
                x=[nage],
                y=[nkca],
                mode="markers",
                marker_size=10,
                marker_symbol="square",
                name="Sink",
            )
        )
        fig.add_trace(
            go.Contour(z=array(full_probability), x=pxs, y=pys, coloraxis="coloraxis")
        )
        fig.add_trace(go.Scatter(x=sxs, y=sys, mode="markers"))
        # fig.update(layout_coloraxis_showscale=False)
        fig.update_coloraxes(showscale=False)
        fig.update_layout(showlegend=False)
        graphjson = fig.to_json()

        fig = go.Figure()
        fig.layout.xaxis.title = "Age (Ma)"
        fig.layout.yaxis.title = "K/Ca"
        fig.layout.margin = {"l": 80, "r": 0, "t": 70, "b": 0}
        fig.layout.title = {
            "text": "Decision Function",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        }

        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers"))
        fig.add_trace(go.Scatter(x=sxs, y=sys, mode="markers"))
        fig.add_trace(go.Contour(z=array(decision_function), x=pxs, y=pys))
        fig.update_layout(showlegend=False)
        graphjson_decision_function = fig.to_json()

    return templates.TemplateResponse(
        "source_sink.html",
        {
            "request": request,
            "age": age,
            "kca": kca,
            "match": match,
            "graphJSON": graphjson,
            "graphJSON_decision_function": graphjson_decision_function,
        },
    )


@app.get("/", response_class=HTMLResponse)
def map_view(request: Request):
    return templates.TemplateResponse(
        "map_view.html",
        {
            "request": request,
            # "center": {"lat": 34.5, "lon": -106.0},
            # "zoom": 7,
            # "data_url": "/locations/fc",
        },
    )


@app.get("/tabular", response_class=HTMLResponse)
def map_view(request: Request):
    return templates.TemplateResponse(
        "table_view.html",
        {
            "request": request,
            # "center": {"lat": 34.5, "lon": -106.0},
            # "zoom": 7,
            # "data_url": "/locations/fc",
        },
    )


@app.get(f"{API_PREFIX}/health")
def get_health():
    return {"status": "ok", "server_time": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8008)
# ============= EOF =============================================
