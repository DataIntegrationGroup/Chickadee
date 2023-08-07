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
from typing import List

from geoalchemy2 import Geometry
from sklearn import svm

from fastapi import APIRouter, Depends
from sklearn.inspection import DecisionBoundaryDisplay
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy import or_
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY

from constants import API_PREFIX, API_VERSION
from models.analysis import Analysis, AnalysisProperty
from models.sample import Sample as MSample, Material as MMaterial
from dependencies import get_db
from routes import Query
from schemas.sample import Sample, Material, CreateSample, GeoJSONFeatureCollection

router = APIRouter(prefix=f"{API_PREFIX}/sample", tags=["Sample"])


@router.get("/geojson", response_model=GeoJSONFeatureCollection)
def get_samples_geojson(db: Session = Depends(get_db)):
    q = Query(db, MSample)

    def togeojson(sample):
        return {
            "type": "Feature",
            "properties": {
                "name": sample.name,
                "project": sample.project.name,
                "material": sample.material.name,
                # "well_depth": {"value": w.WellDepth, "units": "ft"},
            },
            "geometry": sample.geometry,
        }

    content = {
        "features": [togeojson(l) for l in q.all()],
    }

    return content


@router.get("", response_model=List[Sample])
async def root(name: str = None, db: Session = Depends(get_db)):
    q = Query(db, MSample)
    q.add_name_query(name)
    return q.all()


@router.post("/add", response_model=Sample)
async def create_sample(sample: CreateSample, db: Session = Depends(get_db)):
    print("sfas", sample)
    q = Query(db, MSample)
    q.add_name_query(sample.name)
    print(q.all())
    if q.all():
        return Response(status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    params = sample.model_dump()

    params["location"] = "SRID=4326;POINT({} {})".format(
        params.pop("longitude"), params.pop("latitude")
    )

    params["slug"] = params["name"].replace(" ", "_")
    project = params.pop("project")
    params["project_slug"] = project.replace(" ", "_")
    material = params.pop("material")
    params["material_slug"] = material.replace(" ", "_")
    dbsample = MSample(**params)
    dbsample = q.add(dbsample)
    return dbsample


from numpy import (
    linspace,
    zeros,
    full,
    exp,
    pi,
    argmax,
    mean,
    array,
    std,
    column_stack,
    arange,
    isnan,
    c_,
    meshgrid,
    unique,
)
from scipy.stats import kstest, norm, ttest_ind

# def cumulative_probability(ages, errors, xmi, xma, n=100):
#     x = linspace(xmi, xma, n)
#     probs = zeros(n)
#
#     for ai, ei in zip(ages, errors):
#         if abs(ai) < 1e-10 or abs(ei) < 1e-10:
#             continue
#
#         # calculate probability curve for ai+/-ei
#         # p=1/(2*pi*sigma2) *exp (-(x-u)**2)/(2*sigma2)
#         # see http://en.wikipedia.org/wiki/Normal_distribution
#         ds = (x - full(n, ai)) ** 2
#         es2 = full(n, 2 * ei * ei)
#         gs = (es2 * pi) ** -0.5 * exp(-ds / es2)
#
#         # cumulate probabilities
#         # numpy element_wise addition
#         probs += gs
#
#     return x, probs

PLOT = False
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
    PLOT = False

ANS = None


def get_analyses():
    global ANS
    if ANS:
        ans = ANS
    else:
        db = next(get_db())
        q = db.query(AnalysisProperty)
        q = q.join(Analysis)
        q = q.join(MSample)
        # q = q.filter(MSample.slug == si.slug)
        q = q.filter(
            or_(AnalysisProperty.slug == "age", AnalysisProperty.slug == "kca")
        )

        ans = q.all()

    ANS = ans
    return ans


get_analyses()


@router.get("/source_match")
async def match_to_source(
    age: str = None, kca: str = None, db: Session = Depends(get_db)
):
    if age:
        age, age_error = [float(a) for a in age.split(",")]
    if kca:
        kca, kca_error = [float(a) for a in kca.split(",")]

    xmin = age * 0.75
    xmax = age * 1.25
    ymin = kca * 0.75
    ymax = kca * 1.25

    # q = Query(db, MSample)
    # samples = q.all()
    n = 100
    # for si in samples:

    ans = ANS
    ages = array([a.value for a in ans if a.slug == "age"])
    age_errors = [a.error for a in ans if a.slug == "age"]

    kcas = [a.value for a in ans if a.slug == "kca"]
    kca_errors = [a.error for a in ans if a.slug == "kca"]

    # xmin = min(ages)
    # xmax = max(ages)
    # ymin = min(kcas)
    # ymax = max(kcas)

    # idx, ages = array([ for i, a in enumerate(ages) if xmin <= a <= xmax]).T
    idx = [xmin <= a <= xmax for a in ages]
    ages = ages[idx]
    kcas = array(kcas)[idx]

    x = column_stack((ages, kcas))
    ynames = array([a.analysis.sample_slug for a in ans if a.slug == "age"])
    ynames = ynames[idx]

    nys = []
    ys = []
    i = 0
    for yi in ynames:
        if yi in ys:
            nys.append(ys.index(yi))
        else:
            ys.append(yi)
            nys.append(i)
            i += 1

    y = nys
    if PLOT:
        plt.scatter(ages, kcas, c=y, edgecolors="k", cmap="jet")
        plt.plot([age], [kca], "ro")

    nstep = 100
    xx = linspace(xmin, xmax, nstep)
    yy = linspace(ymin, ymax, nstep).T
    xx, yy = meshgrid(xx, yy)
    Xfull = c_[xx.ravel(), yy.ravel()]
    # x = array([[-1, -1], [-2, -1], [1, 1], [2, 1]])
    # y = array([1, 1, 2, 2])
    # clf = make_pipeline(StandardScaler(), svm.SVC(gamma='auto'))
    # clf.fit(X, y)
    # print(x, y)
    # clf = make_pipeline(StandardScaler(), svm.SVC(gamma=2, C=1, probability=True))
    clf = make_pipeline(StandardScaler(), svm.SVC(probability=True))
    # clf = make_pipeline(StandardScaler(), KNeighborsClassifier(3))
    if unique(y).size == 1:
        prediction = y[0]
        pklass = ys[prediction]
        score = -1
    else:
        try:
            clf.fit(x, y)
        except Exception as e:
            return Response(str(e), status_code=400)

        probs = clf.predict_proba([[age, kca]])[0]

        prediction = clf.predict([[age, kca]])
        k = prediction[0]

        pklass = ys[k]
        score = probs[k]
        # print(prediction, pklass)
        # print(probs[k], max(probas[:, k]))

        # ypred = clf.predict(x)
        idx = y == k
        if PLOT:
            plt.scatter(x[idx, 0], x[idx, 1], marker="+")
            probas = clf.predict_proba(Xfull)
            handle = plt.imshow(
                probas[:, k].reshape((nstep, nstep)),
                extent=(xmin, xmax, ymin, ymax),
                origin="lower",
            )
            # ax = plt.axes([0.15, 0.04, 0.7, 0.05])
            # plt.colorbar(handle, orientation="horizontal")
            plt.show()

    ages = [
        a.value for a in ans if a.slug == "age" and a.analysis.sample_slug == pklass
    ]
    kcas = [
        a.value for a in ans if a.slug == "kca" and a.analysis.sample_slug == pklass
    ]
    # print(mean(ages), std(ages), mean(kcas), std(kcas))

    # zscore = (age - mean(ages))/std(ages)
    # # print(zscore)
    #
    # x, cdf = cumulative_probability(ages, errors, (min(ages) - max(errors)) * 0.95,
    #                                 (max(ages) + max(errors)) * 1.05, n=n)
    # gs = norm(loc=age, scale=age_error).cdf(x)
    #
    # ccdf = []
    # for i, ci in enumerate(cdf):
    #     if not i:
    #         ccdf.append(ci)
    #     else:
    #         ccdf.append(ci + ccdf[i-1])
    #
    # ccdf = array(ccdf)
    # # print(gs, argmax(gs), len(gs))
    # # ds = (x - full(n, age)) ** 2
    # # es2 = full(n, 2 * age_error * age_error)
    # # gs = (es2 * pi) ** -0.5 * exp(-ds / es2)
    # # print(gs, age, age_error)
    # print(ttest_ind(norm(loc=age, scale=age_error).pdf(x), ages, equal_var=False))
    # r = kstest(ccdf/max(ccdf), gs/max(gs))
    # print(r.pvalue, x[argmax(gs)], x[argmax(cdf)], age, age_error, mean(ages), zscore)
    # if r.pvalue > 1e-5:
    #     plt.plot(x, gs/max(gs))
    #     plt.plot(x, ccdf/max(ccdf))
    #     plt.plot(x, norm(loc=age, scale=age_error).pdf(x))
    #     plt.show()
    mage = mean(ages)
    mkca = mean(kcas)
    age_zscore = (age - mage) / std(ages)
    kca_zscore = (kca - mkca) / std(kcas)
    return {
        "source": {
            "name": pklass,
            "mean_age": mage,
            "mean_kca": mkca,
            "probability_score": score,
            "age_zscore": age_zscore,
            "kca_zscore": kca_zscore,
        },
        "sink": {"age": age, "kca": kca},
    }


# ============= EOF =============================================
