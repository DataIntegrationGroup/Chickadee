# ===============================================================================
# Copyright 2023 ross
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

from typing import List

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY

from constants import API_PREFIX, API_VERSION
from dependencies import get_db
from models.analysis import Analysis as MAnalysis, AnalysisProperty as MAnalysisProperty
from routes import Query
from schemas.analysis import Analysis, CreateAnalysis, AnalysisProperty

router = APIRouter(prefix=f"{API_PREFIX}/analysis", tags=["analysis"])


@router.get("", response_model=List)
async def root(name: str = None, query: str = None, db: Session = Depends(get_db)):
    q = Query(db, MAnalysis)
    q.add_name_query(name)
    q.add_property_query(query, MAnalysisProperty)
    if query:

        def factory(o):
            obj = Analysis.model_validate(o)
            obj.properties = [
                AnalysisProperty.model_validate(oi)
                for oi in o.properties
                if oi.slug in query
            ]
            return obj

    else:

        def factory(o):
            return Analysis.model_validate(o)

    return [factory(ai) for ai in q.all()]


@router.post("", response_model=Analysis)
async def create(analysis: CreateAnalysis, db: Session = Depends(get_db)):
    q = Query(db, MAnalysis)
    q.add_slug_query(analysis.slug)
    # q.add_name_query(analysis.analysis_name)

    if q.all():
        return Response(status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    params = analysis.model_dump()
    analysis_type = params.pop("analysis_type")
    is_bad = params.pop("is_bad")
    properties = params.pop("properties")

    params["sample_slug"] = params["sample_slug"].replace(" ", "_")
    params["slug"] = params["name"].replace(" ", "_")
    # sample = params.pop('sample')
    # params["slug"] = params["name"].replace(" ", "_")
    print(params)
    an = q.add(MAnalysis(**params))

    for k, v in properties.items():
        prop = AnalysisProperty()
        prop.analysis_slug = an.slug

        prop.slug = k.replace(" ", "_")
        prop.name = k

        vv = v["value"]
        if isinstance(vv, str):
            prop.value_str = vv
        elif isinstance(vv, float):
            prop.value = vv
            prop.error = v["error"]
        elif isinstance(vv, bool):
            prop.value_bool = vv
        elif isinstance(vv, int):
            prop.value_int = vv

        prop.units = v["units"]
        q.add(prop)

    return an


# ============= EOF =============================================
