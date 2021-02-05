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
import unittest
from mockito import mock, when, unstub, ANY, verify
import wp.project.docker_hub as sut


class DockerHubTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.dummy_image_name = "wordpress"
        self.expected_uri = f"https://hub.docker.com/v2/repositories/library/{self.dummy_image_name}/tags?page_size=100"

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        unstub()

    def test_fetch_tags_for_error_response(self):
        response = mock({
            "status_code": 500,
            "text": "TEST Error"
        }, spec=requests.Response)
        when(requests).get(ANY(str)).thenReturn(response)

        with self.assertRaises(RuntimeError):
            sut.fetch_tags(self.dummy_image_name)

        verify(requests, times=1).get(self.expected_uri)

    def test_fetch_tags(self):
        with open(os.path.dirname(__file__) + "/../resources/wordpress-tag-list.json", 'r') as f:
            dummy_response = f.read()

        expected_tag_amount = 1058
        response = mock({
            "status_code": 200,
            "text": dummy_response
        }, spec=requests.Response)
        when(requests).get(ANY(str)).thenReturn(response)

        result = sut.fetch_tags(self.dummy_image_name)
        self.assertIsNotNone(result)
        self.assertEqual(expected_tag_amount, result["count"])
        self.assertEqual(100, len(result["results"]))

        verify(requests, times=1).get(self.expected_uri)

    def test_filter_tags(self):
        name_filter = "apache"
        expected_results = 20
        with open(os.path.dirname(__file__) + "/../resources/wordpress-tag-list.json", 'r') as f:
            dummy_tags = json.loads(f.read())

        result = sut.filter_tags(dummy_tags, name_filter)
        self.assertIsNotNone(result)
        self.assertEqual(expected_results, len(result))

    def test_filter_tags_with_regex(self):
        name_filter = r"[0-9]+\.[0-9]+\.[0-9]-apache"
        expected_results = 2
        with open(os.path.dirname(__file__) + "/../resources/wordpress-tag-list.json", 'r') as f:
            dummy_tags = json.loads(f.read())

        result = sut.filter_tags_regex(dummy_tags, name_filter)
        self.assertIsNotNone(result)
        self.assertEqual(expected_results, len(result))

    def test_determine_highest_version(self):
        dummy_tags = [{"id": 42, "name": "5.4.1-apache"},
                      {"id": 21, "name": "5.4.2-apache"},
                      {"id": 36, "name": "5.4.0-apache"}]
        expected_result = "5.4.2-apache"

        result = sut.determine_highest_version(dummy_tags)
        self.assertIsNotNone(result)
        self.assertEqual(expected_result, result)

    def test_filter_version_name(self):
        self.assertEqual("5.4.1", sut.filter_version_name("5.4.1"))
        self.assertEqual("5.5", sut.filter_version_name("5.5.0"))
        self.assertEqual("5.0", sut.filter_version_name("5.0.0"))


if __name__ == '__main__':
    unittest.main()
