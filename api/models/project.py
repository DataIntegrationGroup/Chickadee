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
from . import Base, EmbargoMixin, SlugMixin
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship


class Project(Base, EmbargoMixin, SlugMixin):
    __tablename__ = "projecttbl"
    # slug = Column(String(80), unique=True, nullable=False, primary_key=True)
    # name = Column(String(80), nullable=False)

    samples = relationship("Sample", backref="project", lazy=True)
    properties = relationship("ProjectProperties", backref="project", lazy=True)
    researchers = relationship("ResearcherProject", backref="project", lazy=True)


class ProjectProperties(Base):
    __tablename__ = "projectpropertytbl"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_slug = Column(String(80), ForeignKey("projecttbl.slug"))
    slug = Column(String(80), unique=True, nullable=False)
    value = Column(String(80), nullable=False)


class Researcher(Base, SlugMixin):
    __tablename__ = "researchertbl"

    orcid = Column(String(80), nullable=True)
    projects = relationship("ResearcherProject", backref="researcher", lazy=True)


class ResearcherProject(Base):
    __tablename__ = "researcherprojecttbl"
    id = Column(Integer, primary_key=True, autoincrement=True)
    researcher_slug = Column(String(80), ForeignKey("researchertbl.slug"))
    project_slug = Column(String(80), ForeignKey("projecttbl.slug"))


# ============= EOF =============================================
