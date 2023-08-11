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
from itertools import groupby
from operator import or_

from constants import API_PREFIX, API_VERSION
from models.analysis import Analysis, AnalysisProperty
from models.sample import Sample as MSample, Material as MMaterial, SampleProperty
from dependencies import get_db
from routes import Query, make_properties
from schemas.sample import Sample, Material, CreateSample, GeoJSONFeatureCollection

from fastapi import Depends, APIRouter
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
from sklearn import svm
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session
from starlette.responses import Response

from models.analysis import AnalysisProperty, Analysis
from dependencies import get_db

router = APIRouter(prefix=f"{API_PREFIX}/process", tags=["process"])

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
    return source_matcher(age, kca)


def source_matcher(age, kca):
    if age:
        if "," in age:
            age, age_error = [float(a) for a in age.split(",")]
        else:
            age, age_error = float(age), 0.0
    if kca:
        if "," in kca:
            kca, kca_error = [float(a) for a in kca.split(",")]
        else:
            kca, kca_error = float(kca), 0.0

    xmin = age * 0.95
    xmax = age * 1.05

    ans = ANS
    ages = array([a.value for a in ans if a.slug == "age"])
    age_errors = [a.error for a in ans if a.slug == "age"]

    kcas = [a.value for a in ans if a.slug == "kca"]
    kca_errors = [a.error for a in ans if a.slug == "kca"]

    idx = [xmin <= a <= xmax for a in ages]
    ages = ages[idx]
    kcas = array(kcas)[idx]

    aes = array(age_errors)[idx]
    kes = array(kca_errors)[idx]

    ymin = min(kcas)
    ymax = max(kcas)

    x = column_stack((ages, kcas))
    ynames = array([a.analysis.sample_slug for a in ans if a.slug == "age"])
    ynames = ynames[idx]

    nys = []
    ylabels = []
    i = 0
    for yi in ynames:
        if yi in ylabels:
            nys.append(ylabels.index(yi))
        else:
            ylabels.append(yi)
            nys.append(i)
            i += 1

    # y = nys
    data = column_stack((ages, kcas, nys))

    def key(i):
        return i[2]

    min_dis = 1e10
    best_klass = None
    distances = {}
    for klass, items in groupby(sorted(data, key=key), key=key):
        items = list(items)

        dis = mean(
            [
                ((10 * (age - a) / age) ** 2 + ((kca - k) / kca) ** 2) ** 0.5
                for a, k, y in items
            ]
        )
        distances[ylabels[int(klass)]] = dis

        if dis < min_dis:
            min_dis = dis
            best_klass_idx = int(klass)
            best_klass = ylabels[best_klass_idx]

    nstep = 100
    lxx = linspace(xmin, xmax, nstep)
    lyy = linspace(ymin, ymax, nstep)
    xx, yy = meshgrid(lxx, lyy)
    Xfull = c_[xx.ravel(), yy.ravel()]

    clf = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", svm.SVC(gamma=1, probability=True)),
        ]
    )
    if unique(nys).size == 1:
        prediction = nys[0]
        pklass = ylabels[prediction]
        score = -1
        probas = zeros((nstep, nstep))
        df = zeros((nstep, nstep))
    else:
        clf.fit(x, nys, classifier__sample_weight=1 / (aes**2 + kes**2))

        probs = clf.predict_proba([[age, kca]])[0]

        prediction = clf.predict([[age, kca]])
        k = prediction[0]

        pklass = ylabels[k]
        score = probs[k]

        probas = clf.predict_proba(Xfull)
        probas = probas[:, k].reshape((nstep, nstep))

        df = clf.decision_function(Xfull)
        df = df[:, k].reshape((nstep, nstep))

    source_ages = [
        a.value for a in ans if a.slug == "age" and a.analysis.sample_slug == pklass
    ]
    source_kcas = [
        a.value for a in ans if a.slug == "kca" and a.analysis.sample_slug == pklass
    ]

    bxs = [
        a.value for a in ans if a.slug == "age" and a.analysis.sample_slug == best_klass
    ]
    bys = [
        a.value for a in ans if a.slug == "kca" and a.analysis.sample_slug == best_klass
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
    mage = mean(source_ages)
    mkca = mean(source_kcas)
    age_zscore = (age - mage) / std(source_ages)
    kca_zscore = (kca - mkca) / std(source_kcas)

    return {
        "source": {
            "name": pklass,
            "mean_age": mage,
            "mean_kca": mkca,
            "ages": source_ages,
            "kcas": source_kcas,
            "probability_score": score,
            "age_zscore": age_zscore,
            "kca_zscore": kca_zscore,
        },
        "sink": {"age": age, "kca": kca},
        "ages": ages.tolist(),
        "kcas": kcas.tolist(),
        "full_probability": probas.tolist(),
        "decision_function": df.tolist(),
        "pxs": lxx.tolist(),
        "pys": lyy.tolist(),
        "mean_closest": {
            "name": best_klass,
            "ages": bxs,
            "kcas": bys,
            "distances": distances,
        },
    }


# ============= EOF =============================================
