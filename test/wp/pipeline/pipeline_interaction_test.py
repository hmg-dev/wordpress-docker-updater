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

from datetime import datetime
import os
import unittest
import requests
import time
from mockito import mock, when, unstub, ANY, verify
from wp.pipeline.pipeline_interaction import Pipeline
from wp import config as conf


class PipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.dummy_project = "PRJ"
        self.dummy_pipeline_name = "build-dummy-pipeline"
        self.dummy_azure_pat = "totalgeheim"
        self.expected_headers = {"Content-Type": "application/json", "Accept": "application/json"}
        self.expected_credentials = (conf.git_user, self.dummy_azure_pat)
        when(os).getenv("DEVOPS_PAT").thenReturn(self.dummy_azure_pat)
        self.sut = Pipeline(self.dummy_project, self.dummy_pipeline_name)

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        unstub()

    def test_validate_pipeline_for_invalid_name(self):
        expected_url = f"{conf.azure_org}{self.dummy_project}/_apis/build/definitions?api-version=5.1&name={self.dummy_pipeline_name}"
        dummy_result = "{\"count\":0,\"value\":[]}"
        response = mock({"status_code": 200, "text": dummy_result}, spec=requests.Response)
        when(requests).get(ANY(), headers=ANY(), auth=ANY()).thenReturn(response)

        result = self.sut.validate()
        self.assertIsNone(result)

        verify(requests, times=1).get(expected_url, headers=self.expected_headers, auth=self.expected_credentials)
        verify(os, times=1).getenv("DEVOPS_PAT")

    def test_validate_pipeline_for_valid_name(self):
        expected_url = conf.azure_org + self.dummy_project + \
                       "/_apis/build/definitions?api-version=5.1&name=" + self.dummy_pipeline_name
        with open(os.path.dirname(__file__) + "/../resources/pipeline_details.json", 'r') as f:
            dummy_response = f.read()

        response = mock({"status_code": 200, "text": dummy_response}, spec=requests.Response)
        when(requests).get(ANY(), headers=ANY(), auth=ANY()).thenReturn(response)

        result = self.sut.validate()
        self.assertIsNotNone(result)
        self.assertEqual(91, result["id"])
        self.assertEqual("infra-docker-dummy", result["name"])

        verify(requests, times=1).get(expected_url, headers=self.expected_headers, auth=self.expected_credentials)
        verify(os, times=1).getenv("DEVOPS_PAT")

    def test_trigger_build_pipeline(self):
        dummy_pipeline_id = 42
        expected_url = conf.azure_org + self.dummy_project + "/_apis/build/builds?api-version=5.1"
        expected_data = "{\"definition\": {\"id\": " + str(dummy_pipeline_id) + "}}"

        with open(os.path.dirname(__file__) + "/../resources/pipeline_queue_result.json", 'r') as f:
            dummy_response = f.read()

        response = mock({"status_code": 200, "text": dummy_response}, spec=requests.Response)
        when(requests).post(ANY(), data=ANY(), headers=ANY(), auth=ANY()).thenReturn(response)

        result = self.sut.trigger_build(dummy_pipeline_id)
        self.assertIsNotNone(result)
        self.assertEqual(26624, result["id"])
        self.assertEqual("notStarted", result["status"])
        self.assertEqual("20200512.1", result["buildNumber"])

        verify(requests, times=1).post(expected_url, data=expected_data, headers=self.expected_headers,
                                      auth=self.expected_credentials)
        verify(os, times=1).getenv("DEVOPS_PAT")

    def test_fetch_build_status_for_error(self):
        dummy_build_id = 36
        expected_request_invocations = 3
        expected_url = f"{conf.azure_org}{self.dummy_project}/_apis/build/builds/{dummy_build_id}?api-version=5.1"

        response = mock({"status_code": 500, "text": "TEST ERROR"}, spec=requests.Response)
        when(requests).get(ANY(), headers=ANY(), auth=ANY()).thenReturn(response)

        result = self.sut.fetch_build_status(dummy_build_id)
        self.assertIsNone(result)

        verify(requests, times=expected_request_invocations).get(expected_url, headers=self.expected_headers, auth=self.expected_credentials)

    def test_fetch_build_status(self):
        dummy_build_id = 32174
        expected_url = f"{conf.azure_org}{self.dummy_project}/_apis/build/builds/{dummy_build_id}?api-version=5.1"

        with open(os.path.dirname(__file__) + "/../resources/pipeline_build_status.json", 'r') as f:
            dummy_response = f.read()

        response = mock({"status_code": 200, "text": dummy_response}, spec=requests.Response)
        when(requests).get(ANY(), headers=ANY(), auth=ANY()).thenReturn(response)

        result = self.sut.fetch_build_status(dummy_build_id)
        self.assertIsNotNone(result)
        self.assertEqual(32174, result["id"])
        self.assertEqual("completed", result["status"])
        self.assertEqual("succeeded", result["result"])
        self.assertEqual("20200728.3", result["buildNumber"])

        verify(requests, times=1).get(expected_url, headers=self.expected_headers, auth=self.expected_credentials)

    def test_fetch_most_recent_build(self):
        dummy_pipeline_id = 42
        dummy_current_timestamp = datetime.strptime("2020-07-28T14:05:00", "%Y-%m-%dT%H:%M:%S")
        expected_url = f"{conf.azure_org}{self.dummy_project}/_apis/build/builds?api-version=5.1" \
            f"&definitions={dummy_pipeline_id}&$top=1&queryOrder=queueTimeDescending"

        with open(os.path.dirname(__file__) + "/../resources/pipeline_build_list.json", 'r') as f:
            dummy_response = f.read()

        response = mock({"status_code": 200, "text": dummy_response}, spec=requests.Response)
        when(self.sut)._now().thenReturn(dummy_current_timestamp)
        when(requests).get(ANY(), headers=ANY(), auth=ANY()).thenReturn(response)

        result = self.sut.fetch_most_recent_build(dummy_pipeline_id)
        self.assertIsNotNone(result)
        self.assertEqual(32174, result["id"])
        self.assertEqual("completed", result["status"])
        self.assertEqual("succeeded", result["result"])
        self.assertEqual("20200728.3", result["buildNumber"])

        verify(requests, times=1).get(expected_url, headers=self.expected_headers, auth=self.expected_credentials)

    def test_fetch_most_recent_build_for_connection_error(self):
        dummy_pipeline_id = 21
        expected_request_invocations = 3
        expected_url = f"{conf.azure_org}{self.dummy_project}/_apis/build/builds?api-version=5.1" \
                       f"&definitions={dummy_pipeline_id}&$top=1&queryOrder=queueTimeDescending"
        when(requests).get(ANY(), headers=ANY(), auth=ANY()).thenRaise(requests.exceptions.ConnectionError("TEST ERROR"))

        result = self.sut.fetch_most_recent_build(dummy_pipeline_id)
        self.assertIsNone(result)

        verify(requests, times=expected_request_invocations).get(expected_url, headers=self.expected_headers,
                                                                 auth=self.expected_credentials)

    def test_wait_for_build_pipeline(self):
        dummy_validation_result = {"id": 42, "name": self.dummy_pipeline_name}
        dummy_build_status_1 = {"id": 36, "buildNumber": "123", "status": "not started", "result": ""}
        dummy_build_status_2 = {"id": 36, "buildNumber": "123", "status": "running", "result": ""}
        dummy_build_status_3 = {"id": 36, "buildNumber": "123", "status": "running", "result": ""}
        dummy_build_status_4 = {"id": 36, "buildNumber": "123", "status": "completed", "result": "succeeded"}
        expected_result = "succeeded"

        when(time).sleep(ANY())
        when(self.sut).validate().thenReturn(dummy_validation_result)
        when(self.sut).fetch_most_recent_build(ANY()).thenReturn(dummy_build_status_1)
        when(self.sut).fetch_build_status(ANY()).thenReturn(
            dummy_build_status_2, dummy_build_status_3, dummy_build_status_4)

        result = self.sut.wait_for_build_pipeline()
        self.assertEqual(expected_result, result)

        verify(self.sut, times=1).validate()
        verify(self.sut, times=1).fetch_most_recent_build(42)
        verify(self.sut, times=3).fetch_build_status(36)
        verify(time, times=3).sleep(10)

    def test_trigger_build_and_wait(self):
        dummy_pipeline_id = 42
        dummy_pipeline_details = {"id": dummy_pipeline_id}
        dummy_build_status = {"id": 36}
        dummy_result_status = "succeeded"
        when(self.sut).validate().thenReturn(dummy_pipeline_details)
        when(self.sut).trigger_build(ANY()).thenReturn(dummy_build_status)
        when(self.sut).wait_for_build_with_id(ANY(), ANY()).thenReturn(dummy_result_status)

        result = self.sut.trigger_build_and_wait()
        self.assertEqual(dummy_result_status, result)

        verify(self.sut, times=1).validate()
        verify(self.sut, times=1).trigger_build(dummy_pipeline_id)
        verify(self.sut, times=1).wait_for_build_with_id(36, {})


if __name__ == '__main__':
    unittest.main()
