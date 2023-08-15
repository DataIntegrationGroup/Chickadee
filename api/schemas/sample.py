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
from typing import Optional

from pydantic import BaseModel, Field

from . import NamedModel


class Sample(NamedModel):
    project_slug: str
    material_slug: str
    latitude: float
    longitude: float
    publication: Optional[str] = None
    doi: Optional[str] = None


class SampleProperty(BaseModel):
    slug: str
    value: Optional[float] = None
    error: Optional[float] = None
    units: Optional[str] = None
    value_str: Optional[str] = None
    value_int: Optional[int] = None
    value_bool: Optional[bool] = None


class SampleDetail(Sample):
    properties: list[SampleProperty] = Field(default_factory=list)


class CreateSample(NamedModel):
    project: str
    material: str
    latitude: float
    longitude: float
    properties: dict = Field(default_factory=dict)
    publication: Optional[str] = None
    doi: Optional[str] = None


class Material(NamedModel):
    pass


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list = Field(..., alias="features")


# ============= EOF =============================================
