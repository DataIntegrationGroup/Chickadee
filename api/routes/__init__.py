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

from sqlalchemy import intersect, union
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.sql.sqltypes import NullType, String as SQLString, DateTime


class StringLiteral(SQLString):
    """Teach SA how to literalize various things."""

    def literal_processor(self, dialect):
        super_processor = super(StringLiteral, self).literal_processor(dialect)

        def process(value):
            if isinstance(value, int):
                return str(value)
            if not isinstance(value, str):
                value = str(value)
            result = super_processor(value)
            if isinstance(result, bytes):
                result = result.decode(dialect.encoding)
            return result

        return process


class LiteralDialect(DefaultDialect):
    colspecs = {
        # prevent various encoding explosions
        # String: StringLiteral,
        # teach SA about how to literalize a datetime
        DateTime: StringLiteral,
        # don't format py2 long integers to NULL
        NullType: StringLiteral,
    }


def literalquery(statement):
    """NOTE: This is entirely insecure. DO NOT execute the resulting strings."""
    # import sqlalchemy.orm
    # if isinstance(statement, sqlalchemy.orm.Query):
    #     statement = statement.statement

    return statement.compile(
        dialect=LiteralDialect(),
        compile_kwargs={"literal_binds": True},
    ).string


def compile_query(query):
    return literalquery(query.statement)


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
        print(compile_query(self.q))

        return self.q.all()

    def add_embargo_query(self, embargoed):
        q = self.q
        now = datetime.now()
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

    def add_property_query(self, query, property_table):
        """
        query is of the form  slug comp value
        e.g. age > 10


        :param query:
        :param property_table:
        :return:
        """
        q = self.q

        f = None
        if query:
            subqueries = []
            if " or " in query:
                tag = ' or '
                agg = union
            else:
                tag = ' and '
                agg = intersect

            for qi in query.split(tag):
                subq = self.db.query(self.table)
                subq = subq.join(property_table)

                slug, comp, value = qi.split(" ")

                if comp == "==":
                    f = property_table.value == value
                elif comp == ">=":
                    f = property_table.value >= float(value)
                elif comp == "<=":
                    f = property_table.value <= float(value)
                elif comp == ">":
                    f = property_table.value > float(value)
                elif comp == "<":
                    f = property_table.value < float(value)

                subq = subq.filter(property_table.slug == slug)
                if f is not None:
                    subqueries.append(subq.filter(f).subquery())

            if subqueries:
                q = q.filter(self.table.slug.in_(agg(*subqueries)))

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
