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
import csv

import requests

from geo_utils import utm_to_latlon


def test(v, t="yes"):
    return v.lower() == t.lower()


def extract():
    p = "./testdata/NMGeochron2022_samples.csv"
    with open(p, "r") as rfile:
        reader = csv.DictReader(rfile)
        for i, row in enumerate(reader):
            if i < 2:
                continue
            yield row


def transform(data):
    for row in data:
        if not test(row["Include Sparrow"]):
            continue

        # if not test(row['Complete']):
        #     continue

        if not (row["Latitude"] and row["Longitude"]):
            e = row["Easting"]
            n = row["Northing"]

            if not (e and n):
                continue

            zone = row["Zone"]
            datum = row.get("Datum")
            if datum:
                datum = datum.upper().replace(" ", "")
            if not zone:
                zone = 13
            lat, lon = utm_to_latlon(e, n, zone=zone, datum=datum)
            row["Latitude"] = lat
            row["Longitude"] = lon
        yield row


def load(data):
    for row in data:
        requests.post(
            "http://localhost:4039/api/v1/material/add", json=make_material_payload(row)
        )
        requests.post(
            "http://localhost:4039/api/v1/project/add", json=make_project_payload(row)
        )
        requests.post(
            "http://localhost:4039/api/v1/sample/add", json=make_sample_payload(row)
        )


def make_project_payload(row):
    return {"name": row["Project"]}


def make_material_payload(row):
    return {"name": row["Material"]}


def make_sample_payload(row):
    return {
        "name": row["Sample"],
        "material": row["Material"],
        "project": row["Project"],
        "latitude": row["Latitude"],
        "longitude": row["Longitude"],
    }


def etl():
    load(transform(extract()))


if __name__ == "__main__":
    etl()
# ============= EOF =============================================
