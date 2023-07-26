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
from sklearn import svm

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY

from models.analysis import Analysis, AnalysisProperty
from models.sample import Sample as MSample, Material as MMaterial
from dependencies import get_db
from routes import Query
from schemas.sample import Sample, Material, CreateSample

router = APIRouter(prefix="/sample", tags=["sample"])


@router.get("", response_model=List[Sample])
async def root(name: str = None, db: Session = Depends(get_db)):
    q = Query(db, MSample)
    q.add_name_query(name)
    return q.all()


@router.post("", response_model=Sample)
async def create_sample(sample: CreateSample, db: Session = Depends(get_db)):
    q = Query(db, MSample)
    q.add_name_query(sample.name)
    if q.all():
        return Response(status_code=HTTP_422_UNPROCESSABLE_ENTITY)

    params = sample.model_dump()
    params["slug"] = params["name"].replace(" ", "_")
    project = params.pop("project")
    params["project_slug"] = project.replace(" ", "_")
    material = params.pop("material")
    params["material_slug"] = material.replace(" ", "_")
    dbsample = MSample(**params)
    dbsample = q.add(dbsample)
    return dbsample


from numpy import linspace, zeros, full, exp, pi, argmax, mean, array, std, column_stack
from scipy.stats import kstest, norm, ttest_ind


def cumulative_probability(ages, errors, xmi, xma, n=100):
    x = linspace(xmi, xma, n)
    probs = zeros(n)

    for ai, ei in zip(ages, errors):
        if abs(ai) < 1e-10 or abs(ei) < 1e-10:
            continue

        # calculate probability curve for ai+/-ei
        # p=1/(2*pi*sigma2) *exp (-(x-u)**2)/(2*sigma2)
        # see http://en.wikipedia.org/wiki/Normal_distribution
        ds = (x - full(n, ai)) ** 2
        es2 = full(n, 2 * ei * ei)
        gs = (es2 * pi) ** -0.5 * exp(-ds / es2)

        # cumulate probabilities
        # numpy element_wise addition
        probs += gs

    return x, probs


# import matplotlib.pyplot as plt


@router.get("/source_match")
async def match_to_source(
    age: str = None, kca: str = None, db: Session = Depends(get_db)
):
    if age:
        age, age_error = [float(a) for a in age.split(",")]
    if kca:
        kca, kca_error = [float(a) for a in kca.split(",")]

    q = Query(db, MSample)
    samples = q.all()
    n = 100
    for si in samples:
        q = db.query(AnalysisProperty)
        q = q.join(Analysis)
        q = q.join(MSample)
        q = q.filter(MSample.slug == si.slug)
        q = q.filter(
            or_(AnalysisProperty.slug == "age", AnalysisProperty.slug == "kca")
        )

        ans = q.all()

        ages = [a.value for a in ans if a.slug == "age"]
        age_errors = [a.error for a in ans if a.slug == "age"]

        kcas = [a.value for a in ans if a.slug == "kca"]
        kca_errors = [a.error for a in ans if a.slug == "kca"]

        x = column_stack((ages, kcas))
        y = [a.analysis.name for a in ans if a.slug == "age"]

        clf = svm.SVC()
        clf.fit(x, y)
        print(clf.predict([[age, kca]]))

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

    return "ok"


# ============= EOF =============================================
