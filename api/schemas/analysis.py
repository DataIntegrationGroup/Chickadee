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
from datetime import datetime

from pydantic import Extra

from . import NamedModel, ORMBaseModel


class Analysis(ORMBaseModel, extra=Extra.allow):
    # analysis_type: str
    # name: str
    slug: str
    sample_slug: str
    timestamp: datetime
    # is_bad: bool = False
    # properties: dict = None


class CreateAnalysis(ORMBaseModel):
    analysis_type: str
    name: str
    slug: str
    sample_slug: str
    timestamp: datetime
    is_bad: bool = False
    properties: dict = None


class AnalysisProperty(ORMBaseModel):
    slug: str
    value: float
    error: float
    units: str = None


# ============= EOF =============================================
