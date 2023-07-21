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
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import sample
from dependencies import get_db
from schemas.sample import Sample

router = APIRouter(prefix="/sample", tags=["sample"])


@router.get("/", response_model=list[Sample])
async def root(db: Session = Depends(get_db)):
    q = db.query(sample.Sample)
    samples = q.all()

    return samples


# ============= EOF =============================================
