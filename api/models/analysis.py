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
from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Boolean, Integer
from models import Base
from models.sample import SlugMixin


class Analysis(Base, SlugMixin):
    __tablename__ = "analysistbl"

    sample_slug = Column(String(80), ForeignKey("sampletbl.slug"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    lab_id = Column(String(80), nullable=False)


class AnalysisProperty(Base, SlugMixin):
    __tablename__ = "analysispropertytbl"
    analysis_id = Column(String(80), ForeignKey("analysistbl.slug"), nullable=False)
    value = Column(Float, nullable=True)
    value_str = Column(String(80), nullable=True)
    value_bool = Column(Boolean, nullable=True)
    value_int = Column(Integer, nullable=True)
# ============= EOF =============================================
