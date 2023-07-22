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
from app import app

from database import engine
from models import sample, project, analysis, Base

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


from routes import sample, project, analysis
app.include_router(sample.router)
app.include_router(project.router)
app.include_router(analysis.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8008)
# ============= EOF =============================================
