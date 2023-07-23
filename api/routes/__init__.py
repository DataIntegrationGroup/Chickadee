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


class Query:
    def __init__(self, db, table):
        self.db = db
        self.table = table
        self.q = db.query(table)

    def add(self, item):
        db = self.db
        db.add(item)
        db.commit()
        # db.refresh_item(item)
        return item

    def all(self):
        return self.q.all()

    def add_embaro_query(self, embargoed):
        q = self.q
        now = datetime.datetime.now()
        if embargoed is not None:
            q = q.filter(self.table.embargo_date > now.date())
        self.q = q

    def add_name_query(self, name):
        q = self.q
        if name:
            q = q.filter(self.table.name == name)
        self.q = q

    def add_slug_query(self, slug):
        q = self.q
        if slug:
            q = q.filter(self.table.slug == slug)
        self.q = q

    def add_property_query(self, query):
        q = self.q
        table = self.table
        f = None
        q = q.join(table)
        query, comp, value = query.split(" ")
        if comp == "==":
            f = table.value == value
        elif comp == ">=":
            f = table.value >= value
        elif comp == "<=":
            f = table.value <= value
        elif comp == ">":
            f = table.value > value
        elif comp == "<":
            f = table.value < value

        if f:
            q = q.filter(f)

        self.q = q


def root_query(name: str, db, table):
    q = db.query(table)
    if name:
        q = q.filter(table.name == name)
    return q.all()

#
# def property_query(q, query, table):
#     f = None
#     q = q.join(table)
#     query, comp, value = query.split(' ')
#     if comp == '==':
#         f = table.value == value
#     elif comp == '>=':
#         f = table.value >= value
#     elif comp == '<=':
#         f = table.value <= value
#     elif comp == '>':
#         f = table.value > value
#     elif comp == '<':
#         f = table.value < value
#
#     if f:
#         q = q.filter(f)
#     return q
# ============= EOF =============================================
