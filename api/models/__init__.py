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

from sqlalchemy import Column, String, DateTime, func, Date, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

Base = declarative_base()


class SlugMixin:
    @declared_attr
    def slug(cls):
        return Column(String(80), unique=True, nullable=False, primary_key=True)

    @declared_attr
    def name(cls):
        return Column(String(80), nullable=False)


class PropertyMixin:
    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True, autoincrement=True)

    @declared_attr
    def slug(cls):
        return Column(String(80), unique=False, nullable=False)

    @declared_attr
    def value(cls):
        return Column(Float, nullable=False)

    @declared_attr
    def error(cls):
        return Column(Float, nullable=True)


class EmbargoMixin:
    @property
    def is_embargoed(self):
        return self.embargo_date > datetime.now().date()

    @declared_attr
    def embargo_date(self):
        return Column(Date, nullable=False, server_default=func.now())

    @declared_attr
    def publication(self):
        return Column(String(80), nullable=True)

    @declared_attr
    def doi(self):
        return Column(String(80), nullable=True)


# ============= EOF =============================================
