#!/usr/bin/env python3

# build.py - build steps to be executed before DHParser is packaged with poetry
#
# Copyright 2026  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

import os
import shutil
import subprocess
import sys


def get_env_python() -> str:
    """Find the Python executable of the active virtual environment."""
    # 1. If VIRTUAL_ENV is active, use its Python binary
    if "VIRTUAL_ENV" in os.environ:
        venv_python = os.path.join(os.environ["VIRTUAL_ENV"], "bin", "python")
        if os.path.exists(venv_python):
            return venv_python

    # 2. Otherwise fallback to 'python3' or 'python' found on PATH
    python_on_path = shutil.which("python3") or shutil.which("python")
    if python_on_path:
        return python_on_path

    # 3. Fallback to current process Python
    return sys.executable


def build_docs():
    python_exec = get_env_python()
    print("Building Sphinx documentation...")
    subprocess.check_call([
        python_exec, "-m", "sphinx",
        "-b", "html",
        "documentation_src",
        "DHParser/docs"
    ])


if __name__ == "__main__":
    build_docs()
