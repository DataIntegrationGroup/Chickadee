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
from itertools import groupby

import pandas as pd
from datetime import datetime, time as dtime
from uncertainties import nominal_value, std_dev, ufloat
import requests
from pandas import isnull

from geo_utils import utm_to_latlon

HOST = "localhost"
PORT = 4039


def test(v, t="yes"):
    return v.lower() == t.lower()


def extract():
    p = "./testdata/NMGeochron2022_samples2.csv"
    with open(p, "r") as rfile:
        reader = csv.DictReader(rfile)
        for i, row in enumerate(reader):
            if i < 2:
                continue
            yield row


def extract_ds_analyses():
    p = "/Users/jross/Sandbox/DSCompare/SJVF_sources.xls"
    source_df = pd.read_excel(p, sheet_name="SJVF_sources")
    for i, row in source_df.iterrows():
        yield row.to_dict()


def extract_ds():
    p = "/Users/jross/Sandbox/DSCompare/SJVF_sources.xls"
    source_summary_df = pd.read_excel(p, sheet_name="summary")

    for i, su in source_summary_df.iterrows():
        yield su.to_dict()


def transform_ds(data):
    for row in data:
        row["Material"] = row["min"]
        row["Project"] = "SanJuan Volcanic Field"
        row["Latitude"] = row.get("Latitude", 35)
        row["Longitude"] = row.get("Longitude", -106)
        yield row


def transform_analyses_ds(data):
    for row in data:
        if isnull(row["Sample"]):
            break
        yield row


def transform_samples_ds(data):
    for row in data:
        if isnull(row["Sample"]):
            break
        yield row


def transform(data):
    for row in data:
        if not test(row["Include Sparrow"]):
            continue

        if not row['Project']:
            continue

        # if not test(row['Complete']):
        #     continue
        for k, ki, cast in (
            ("age", "Assigned Age", float),
            ("age_err", "Assigned Age Error", float),
            ("kca", "K/Ca", float),
            ("kca_err", "K/Ca Error", float),
            ('age_interpretation', "Assigned Age Interpretation", str),
        ):
            v = row[ki].strip()
            try:
                row[k] = cast(v)
            except ValueError:
                row[k] = -1

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
            lon, lat = utm_to_latlon(e, n, zone=zone, datum=datum)
            row["Latitude"] = lat
            row["Longitude"] = lon
        print("yiea", row)
        yield row


def load(data):
    # host = "129.138.12.35"

    for row in data:
        print(
            requests.post(
                f"http://{HOST}:{PORT}/api/v1/material/add",
                json=make_material_payload(row),
            )
        )
        print(
            requests.post(
                f"http://{HOST}:{PORT}/api/v1/project/add",
                json=make_project_payload(row),
            )
        )
        print(
            requests.post(
                f"http://{HOST}:{PORT}/api/v1/sample/add", json=make_sample_payload(row)
            )
        )


def load_ds_samples(data):
    def key(d):
        return d["Sample"]

    # data = [di for di in data if not isnull(di['Sample'])]
    for sample, gs in groupby(sorted(data, key=key), key=key):
        add("material", {"name": "Sanidine"})
        add("project", {"name": "DS"})
        add(
            "sample",
            {
                "name": sample,
                "material": "Sanidine",
                "project": "DS",
                "properties": {},
                "latitude": 35,
                "longitude": -106,
            },
        )

        # requests.post(
        #     f"http://{HOST}:{PORT}/api/v1/material/add", json={'name': 'Sanidine'}
        # )
        # requests.post(
        #     f"http://{HOST}:{PORT}/api/v1/project/add", json={'name': 'DS'}
        # )
        # requests.post(
        #     f"http://{HOST}:{PORT}/api/v1/sample/add", json={'name': sample,
        #                                                      'material': 'Sanidine',
        #                                                      'project': 'DS',
        #                                                      'properties': {},
        #                                                      'latitude': 35,
        #                                                      'longitude': -106}
        # )


def load_ds(data):
    for row in data:
        add("analysis", make_analysis_payload(row))
        # print(row)
        # print(make_analysis_payload(row))
        # requests.post(f"http://{HOST}:{PORT}/api/v1/analysis/add", json=make_analysis_payload(row))


def add(endpoint, payload):
    return requests.post(f"http://{HOST}:{PORT}/api/v1/{endpoint}/add", json=payload)


def make_project_payload(row):
    return {"name": row["Project"]}


def make_material_payload(row):
    return {"name": row["Material"]}


def make_sample_payload(row):
    print(row)
    return {
        "name": row["Sample"],
        "material": row["Material"],
        "project": row["Project"],
        "latitude": row["Latitude"],
        "longitude": row["Longitude"],
        "publication": row['Publication'],
        "doi": row['DOI'],
        "properties": {
            "age_interpretation": {"value": row["age_interpretation"] or ""},
            "age": {
                "value": row["age"] or 0,
                "error": row["age_err"] or 0,
                "units": "Ma",
            },
            "kca": {
                "value": row["kca"] or 0,
                "error": row["kca_err"] or 0,
                "units": "",
            },
        },
    }


def make_analysis_payload(row):
    cak = ufloat(row.get("Ca_Over_K", 1), row.get("Ca_Over_K_Er", 1))
    kca = 1 / cak

    runtime = row["Run_Hour"]
    runtime = dtime(hour=int(runtime), minute=int(runtime % 1 * 60))
    rundate = row["Run_Date"]
    dt = datetime.combine(rundate, runtime).isoformat()

    return {
        "is_bad": row.get("tag", "ok").lower() == "invalid",
        "analysis_type": "Fusion",
        "sample_slug": row["Sample"],
        "slug": row["Run_ID"],
        "name": row["Run_ID"],
        "timestamp": dt,
        "properties": {
            "age": {
                "value": row.get("Age", 0),
                "error": row.get("Age_Er", 0),
                "units": "Ma",
            },
            "kca": {"value": nominal_value(kca), "error": std_dev(kca), "units": ""},
            "j": {"value": row.get("J", 0), "error": row.get("J_Er", 0), "units": ""},
        },
    }


def etl():
    load(transform(extract()))


def etl_ds():
    # transform_ds(extract_ds())
    load(transform_ds(extract_ds()))


def etl_analyses_ds():
    # list(transform_analyses_ds(extract_ds_analyses()))
    # load_ds_samples(transform_samples_ds(extract_ds_analyses()))
    load_ds(transform_analyses_ds(extract_ds_analyses()))


if __name__ == "__main__":
    etl()
    # etl_ds()
    # etl_analyses_ds()
# ============= EOF =============================================
