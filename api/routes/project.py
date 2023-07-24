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
import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY

from dependencies import get_db
from models.project import Project as MProject
from routes import root_query, Query
from schemas.project import Project

router = APIRouter(prefix="/project", tags=["project"])


@router.get("", response_model=List[Project])
async def root(
    name: str = None,
    embargoed: bool = None,
    db: Session = Depends(get_db),
):
    q = Query(db, MProject)
    q.add_name_query(name)
    q.add_embargo_query(embargoed)

    # table = project.Project
    #
    # q = db.query(table)
    # if name:
    #     q = q.filter(table.name == name)

    return q.all()

    # return root_query(name, db, project.Project)


@router.post("", response_model=Project)
async def create(project: Project, db: Session = Depends(get_db)):
    q = Query(db, MProject)
    q.add_name_query(project.name)
    if q.all():
        return Response(status_code=HTTP_422_UNPROCESSABLE_ENTITY)
        # raise Exception(f"Project {project.name} already exists")

    params = project.model_dump()
    params["slug"] = params["name"].replace(" ", "_")

    return q.add(MProject(**params))


# ============= EOF =============================================
