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
from geoalchemy2.shape import to_shape
from sqlalchemy import Column, String, Float, Integer, ForeignKey
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship, declared_attr
from . import Base, SlugMixin, EmbargoMixin, PropertyMixin


class Sample(Base, SlugMixin, EmbargoMixin):
    __tablename__ = "sampletbl"

    location = Column(Geometry("POINT", srid=4326), nullable=True)
    project_slug = Column(String(80), ForeignKey("projecttbl.slug"))
    material_slug = Column(String(80), ForeignKey("materialtbl.slug"))

    properties = relationship("SampleProperty", backref="sample", lazy=True)

    @property
    def geometry(self):
        point = to_shape(self.location)
        return {"coordinates": [float(point.x), float(point.y)], "type": "Point"}

    @property
    def latitude(self):
        return to_shape(self.location).y

    @property
    def longitude(self):
        return to_shape(self.location).x


class Material(Base, SlugMixin):
    __tablename__ = "materialtbl"

    properties = relationship("MaterialProperty", backref="material", lazy=True)
    sample = relationship("Sample", backref="material", lazy=True)


class MaterialProperty(Base, PropertyMixin):
    __tablename__ = "materialpropertytbl"

    material_slug = Column(String(80), ForeignKey("materialtbl.slug"))


class SampleProperty(Base, PropertyMixin):
    __tablename__ = "samplepropertytbl"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_slug = Column(String(80), ForeignKey("sampletbl.slug"))


# ============= EOF =============================================
