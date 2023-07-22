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

def root_query(name: str, db, table):
    q = db.query(table)
    if name:
        q = q.filter(table.name == name)
    return q.all()


def property_query(q, query, table):
    f = None
    q = q.join(table)
    query, comp, value = query.split(' ')
    if comp == '==':
        f = table.value == value
    elif comp == '>=':
        f = table.value >= value
    elif comp == '<=':
        f = table.value <= value
    elif comp == '>':
        f = table.value > value
    elif comp == '<':
        f = table.value < value

    if f:
        q = q.filter(f)
    return q
# ============= EOF =============================================