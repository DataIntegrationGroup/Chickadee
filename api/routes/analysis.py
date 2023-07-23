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
from sqlalchemy.orm import Session

from dependencies import get_db
from models import analysis
from routes import Query
from schemas.analysis import Analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get('', response_model=List[Analysis])
async def root(name: str = None,
               query: str = None,
               db: Session = Depends(get_db)):
    q = Query(db, analysis.Analysis)
    q.add_name_query(name)
    q.add_property_query(query)

    return q.all()

# ============= EOF =============================================
