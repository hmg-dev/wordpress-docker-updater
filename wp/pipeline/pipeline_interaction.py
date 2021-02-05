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

import datetime
import json
import os
import requests
import time
from wp import config as conf

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
ENV_DEVOPS_PAT = "DEVOPS_PAT"
HEADERS_JSON = {"Content-Type": "application/json", "Accept": "application/json"}


class Pipeline(object):
    def __init__(self, project, pipeline_name):
        self.project = project
        self.pipeline_name = pipeline_name
        self.credentials = (conf.git_user, os.getenv(ENV_DEVOPS_PAT))

    def validate(self):
        print(f"Validate Pipeline \"{self.pipeline_name}\" for project \"{self.project}\" ...")
        url = f"{conf.azure_org}{self.project}/_apis/build/definitions?api-version=5.1&name={self.pipeline_name}"

        response = requests.get(url, headers=HEADERS_JSON, auth=self.credentials)
        if response.status_code != 200:
            return None

        json_data = json.loads(response.text)
        if json_data["count"] == 0:
            return None

        return json_data["value"][0]

    def trigger_build_and_wait(self):
        pipeline_details = self.validate()
        build_status = self.trigger_build(pipeline_details["id"])
        return self.wait_for_build_with_id(build_status["id"], {})

    def trigger_build(self, pipeline_id):
        print(f"Trigger Build-Pipeline \"{self.pipeline_name}\" for project \"{self.project}\" ...")
        url = f"{conf.azure_org}{self.project}/_apis/build/builds?api-version=5.1"
        data = "{\"definition\": {\"id\": " + str(pipeline_id) + "}}"

        response = requests.post(url, data=data, headers=HEADERS_JSON, auth=self.credentials)
        if response.status_code != 200:
            raise RuntimeError(f"Queue build for pipeline FAILED! Got status code: {response.status_code}")

        return json.loads(response.text)

    def fetch_build_status(self, build_id):
        print(f"fetch status of build {build_id} ...")
        url = f"{conf.azure_org}{self.project}/_apis/build/builds/{build_id}?api-version=5.1"

        response = requests.get(url, headers=HEADERS_JSON, auth=self.credentials)
        if response.status_code != 200:
            print(f"ERROR: Unable to fetch build-status for build {build_id}")
            print(f"Response-Code: {response.status_code}"
                  f"Response-Text: {response.text}")
            return None

        json_data = json.loads(response.text)
        return {"id": json_data["id"], "status": json_data["status"],
                "result": json_data.get("result"), "buildNumber": json_data["buildNumber"]}

    def fetch_most_recent_build(self, pipeline_id):
        print(f"fetch most recent build for pipeline {pipeline_id}")
        url = f"{conf.azure_org}{self.project}/_apis/build/builds?api-version=5.1" \
            f"&definitions={pipeline_id}&$top=1&queryOrder=queueTimeDescending"

        response = requests.get(url, headers=HEADERS_JSON, auth=self.credentials)
        if response.status_code != 200:
            print(f"ERROR: Unable to fetch most recent build for pipeline {pipeline_id}")
            print(f"Response-Code: {response.status_code}"
                  f"Response-Text: {response.text}")
            return None

        json_data = json.loads(response.text)
        if json_data["count"] == 0:
            print(f"ERROR: Unable to fetch most recent build for pipeline {pipeline_id} - count was 0")
            return None

        return json_data["value"][0]

    @staticmethod
    def _now():
        return datetime.datetime.now()

    def wait_for_build_pipeline(self):
        print(f"wait for build of '{self.pipeline_name}' to complete...")
        pipeline_details = self.validate()
        build_status = self.fetch_most_recent_build(pipeline_details["id"])
        build_id = build_status["id"]

        return self.wait_for_build_with_id(build_id, build_status)

    def wait_for_build_with_id(self, build_id, build_status):
        while build_status.get("status") != "completed":
            time.sleep(10)
            build_status = self.fetch_build_status(build_id)
            print(f"build {build_status['id']} is in status {build_status['status']}")

        print(f"build {build_status['id']} finished with result {build_status['result']}")
        return build_status['result']
