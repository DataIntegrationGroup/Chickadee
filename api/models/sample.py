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

from sqlalchemy import Column, String, Float, Integer, ForeignKey
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship, declared_attr
from . import Base


class SlugMixin:
    @declared_attr
    def slug(cls):
        return Column(String(80), unique=True, nullable=False, primary_key=True)

    @declared_attr
    def name(self):
        return Column(String(80), nullable=False)


class Sample(Base, SlugMixin):
    __tablename__ = "sampletbl"

    location = Column(Geometry("POINT", srid=4326), nullable=True)
    project_slug = Column(String(80), ForeignKey("projecttbl.slug"))
    material_slug = Column(String(80), ForeignKey("materialtbl.slug"))

    properties = relationship("Property", backref="sample", lazy=True)


class Material(Base, SlugMixin):
    __tablename__ = "materialtbl"


class MaterialProperty(Base):
    __tablename__ = "materialpropertytbl"
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_slug = Column(String(80), ForeignKey("materialtbl.slug"))


class Property(Base):
    __tablename__ = "propertytbl"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sample_slug = Column(String(80), ForeignKey("sampletbl.slug"))
    slug = Column(String(80), unique=True, nullable=False)
    value = Column(Float, nullable=False)
    error = Column(Float, nullable=True)


# ============= EOF =============================================
