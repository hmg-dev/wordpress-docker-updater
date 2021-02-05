# Copyright (C) 2020, Martin Drößler <m.droessler@handelsblattgroup.com>
# Copyright (C) 2020, Handelsblatt GmbH
#
# This file is part of Docker-Update-Scanner
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from pathlib import Path
import re


class RepoDetails(object):
    DEFAULT_IMAGE_VERSION = "latest"

    def __init__(self, repo):
        self.repo = repo

    @staticmethod
    def determine_imageversion(repo_path):
        print(f"Looking for azure-pipelines.yml in: {repo_path}")
        az_pipeline_file = Path(repo_path, "azure-pipelines.yml")
        if not az_pipeline_file.is_file():
            print("Repo does not contain azure-pipelines.yml")
            return RepoDetails.DEFAULT_IMAGE_VERSION

        with open(az_pipeline_file, 'r') as f:
            return RepoDetails.grep_imageversion(f.readlines(), RepoDetails.DEFAULT_IMAGE_VERSION)

    @staticmethod
    def grep_imageversion(lines, default):
        for line in lines:
            match = re.search(r"[vV]ersion.*:\s*([\"'])?([^\"']*)([\"'])?", line)
            if match is not None:
                return match.group(2).rstrip()

        print("No matching version-line azure-pipelines.yml")
        return default

    @staticmethod
    def determine_parent_image(repo_path):
        dockerfiles = list(Path(repo_path).rglob("Dockerfile"))
        print(f"Found Dockerfile(s): {dockerfiles}")

        with open(dockerfiles[0], 'r') as f:
            return RepoDetails.grep_parent(f.readlines())

    @staticmethod
    def grep_parent(lines):
        for line in lines:
            match = re.search(r"[fF][rR][oO][mM]\s*(.*)", line)
            if match is not None:
                return match.group(1)

        raise RuntimeError("File does not contain expected pattern for parent Docker-Image!")
