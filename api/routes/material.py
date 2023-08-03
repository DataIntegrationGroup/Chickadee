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
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY

from constants import API_PREFIX, API_VERSION
from models.sample import Sample as MSample, Material as MMaterial
from dependencies import get_db
from routes import Query
from schemas.sample import Sample, Material, CreateSample

router = APIRouter(prefix=f"{API_PREFIX}/material", tags=["Material"])


@router.get("", response_model=List[Material])
async def root(name: str = None, db: Session = Depends(get_db)):
    q = Query(db, MMaterial)
    q.add_name_query(name)
    return q.all()


@router.post("", response_model=Material)
async def create_material(material: Material, db: Session = Depends(get_db)):
    q = Query(db, MMaterial)
    q.add_name_query(material.name)
    if q.all():
        return Response(status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    params = material.model_dump()
    params["slug"] = params["name"].replace(" ", "_")

    return q.add(MMaterial(**params))


# ============= EOF =============================================
