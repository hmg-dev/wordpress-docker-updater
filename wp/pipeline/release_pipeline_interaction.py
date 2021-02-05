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

import json
import os
import requests
import urllib.parse
from wp import config as conf

ENV_DEVOPS_PAT = "DEVOPS_PAT"
HEADERS_JSON = {"Content-Type": "application/json", "Accept": "application/json"}


class ReleasePipeline(object):
    def __init__(self, project, pipeline_name):
        self.project = project
        self.pipeline_name = pipeline_name
        self.credentials = (conf.git_user, os.getenv(ENV_DEVOPS_PAT))

    def validate(self):
        print(f"Validate Pipeline \"{self.pipeline_name}\" for project \"{self.project}\" ...")
        search_param = urllib.parse.quote(self.pipeline_name)
        url = f"{conf.azure_org_vs}{self.project}/_apis/release/definitions?api-version=5.1&searchText={search_param}"

        response = requests.get(url, headers=HEADERS_JSON, auth=self.credentials)
        if response.status_code != 200:
            return None

        json_data = json.loads(response.text)
        if json_data["count"] == 0:
            return None

        return json_data["value"][0]

    def trigger_release(self, pipeline_id):
        print(f"Trigger release-pipeline \"{self.pipeline_name}\" for project {self.project}")
        url = f"{conf.azure_org_vs}{self.project}/_apis/release/releases?api-version=5.1"
        data = "{\"definitionId\": " + str(pipeline_id) + ", \"description\": \"auto-update trigger\"}"

        response = requests.post(url, data=data, headers=HEADERS_JSON, auth=self.credentials)
        if response.status_code != 200:
            raise RuntimeError(f"Create Release FAILED! Got status code: {response.status_code}")

        return json.loads(response.text)
