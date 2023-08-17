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
import os


def get_input(msg):
    return input(f"{msg}: ")


def write_file(path, txt):
    with open(path, "w") as wfile:
        wfile.write(txt)


def create_new_integration():
    name = get_input("Integration Name")
    if not name:
        print("Integration name is required")
        return

    print(f"Creating new integration called {name}")

    os.mkdir(f"../{name}")
    os.chdir(f"../{name}")

    p = "main.py"
    txt = """
def main():
    print('hello world')
    
if __name__ == '__main__':
    main()"""

    write_file(p, txt)

    p = "Dockerfile"
    txt = """FROM python:3.9-slim as build-image
LABEL authors="jross"
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.9-slim as run-image
COPY --from=build-image /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

ADD main.py .

CMD ["python", "main.py"]"""
    write_file(p, txt)

    p = "requirements.txt"
    txt = """
requests
"""
    write_file(p, txt)


if __name__ == "__main__":
    create_new_integration()
# ============= EOF =============================================
