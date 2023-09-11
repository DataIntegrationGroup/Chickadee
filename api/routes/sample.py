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
import time
from pathlib import Path
from typing import List, Optional

from geoalchemy2 import Geometry
from sklearn import svm

from fastapi import APIRouter, Depends
from sklearn.inspection import DecisionBoundaryDisplay
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import or_
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, joinedload
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY
from starlette.templating import Jinja2Templates

from constants import API_PREFIX, API_VERSION
from models.sample import Sample as MSample, Material as MMaterial, SampleProperty
from dependencies import get_db
from routes import Query, make_properties, make_property, alter_property
from schemas.sample import (
    Sample,
    Material,
    CreateSample,
    GeoJSONFeatureCollection,
    SampleDetail,
    SampleProperty as SPSchema,
)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(BASE_DIR, "templates")))

router = APIRouter(prefix=f"{API_PREFIX}/sample", tags=["Sample"])


@router.get(
    "/detail/{slug}", response_model=SampleDetail, response_model_exclude_unset=True
)
def get_sample_detail(slug: str, db: Session = Depends(get_db)):
    q = Query(db, MSample)
    q.add_slug_query(slug)
    try:
        return q.one()
    except NoResultFound:
        return {
            "name": "No sample found",
            "slug": slug,
            "project_slug": "No project found",
            "material_slug": "No material found",
            "latitude": 0,
            "longitude": 0,
            "properties": [],
        }


class DummyProperty:
    def model_dump(self):
        return {}


@router.get("/geojson", response_model=GeoJSONFeatureCollection)
def get_samples_geojson(db: Session = Depends(get_db)):
    q = Query(db, MSample)

    def togeojson(sample):
        props = [SPSchema.model_validate(p.__dict__) for p in sample.properties]

        def get_prop(name):
            for p in props:
                if p.slug == name:
                    return p
            else:
                return DummyProperty()

        return {
            "type": "Feature",
            "properties": {
                "name": sample.name,
                "project": sample.project_slug,
                "material": sample.material_slug,
                "age": get_prop("age").model_dump(),
                "kca": get_prop("kca").model_dump(),
            },
            "geometry": sample.geometry,
        }

    st = time.time()
    q.options(joinedload(MSample.properties))
    content = {
        "features": [togeojson(l) for l in q.all()],
    }
    print("geojson", time.time() - st)
    return content


@router.get("")
async def root(name: str = None, properties: str = None, db: Session = Depends(get_db)):
    q = Query(db, MSample)
    q.add_name_query(name)
    q.options(joinedload(MSample.properties))

    def func(r, p):
        return next((prop for prop in r.properties if prop.slug == p), None)

    rs = q.all()
    if properties:
        props = properties.split(",")
        field_definitions = {}
        for p in props:
            if p in ("map_unit", "geologic_unit"):
                field_definitions[p] = (Optional[str], ...)
            else:
                field_definitions[p] = (Optional[float], ...)
                if p in ("age", "kca"):
                    field_definitions[f"{p}_error"] = (Optional[float], ...)
                    if p == "age":
                        field_definitions["age_units"] = (Optional[str], ...)
                        # field_definitions['age_kind'] = (Optional[str], ...)

        for r in rs:
            for p in props:
                pp = func(r, p)

                if p in ("map_unit", "geologic_unit"):
                    setattr(r, p, pp.value_str if pp else "")
                else:
                    if pp:
                        v, e = pp.value, pp.error
                    else:
                        v, e = None, None

                    setattr(r, p, v)
                    if p in ("age", "kca"):
                        setattr(r, f"{p}_error", e)
                        if p == "age":
                            setattr(r, "age_units", pp.units)
                            # setattr(r, 'age_kind', pp.kind)

        model = Sample.with_fields(**field_definitions)
    else:
        model = Sample

    rs = [model.model_validate(r) for r in rs]
    return rs


@router.post("/add", response_model=Sample)
async def create_sample(sample: CreateSample, db: Session = Depends(get_db)):
    print("create sample", sample.name)
    q = Query(db, MSample)
    q.add_name_query(sample.name)
    try:
        dbsam = q.one()
    except NoResultFound:
        dbsam = None

    params = sample.model_dump()

    params["location"] = "SRID=4326;POINT({} {})".format(
        params.pop("longitude"), params.pop("latitude")
    )

    params["slug"] = params["name"].replace(" ", "_")
    project = params.pop("project")
    params["project_slug"] = project.replace(" ", "_")
    material = params.pop("material")
    params["material_slug"] = material.replace(" ", "_")

    properties = params.pop("properties")

    if dbsam:
        print(
            f"sample {sample.name} already exists. trying to patch with new properties"
        )
        print("properties", properties)

        for k, v in properties.items():
            dbprop = next((p for p in dbsam.properties if p.slug == k), None)
            if dbprop:
                alter_property(dbprop, v)
            else:
                prop = make_property(k, v, SampleProperty)
                dbsam.properties.append(prop)

        db.commit()
    else:
        dbsample = MSample(**params)

        props = make_properties(properties, SampleProperty)
        dbsample.properties = props
        dbsam = q.add(dbsample)

    return dbsam


# ============= EOF =============================================
