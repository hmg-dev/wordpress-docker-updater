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
from shutil import copyfile
from tempfile import TemporaryDirectory
from wp.project import wp_plugins as sut


class WpPluginsTest(unittest.TestCase):

    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.dummy_plugin_json = self._create_dummy_plugin_json()

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        unstub()

    def test_read_plugin_list(self):
        with TemporaryDirectory("dummy-repo") as td:
            tmpl_file = "plugin-list.json"
            os.mkdir(f"{td}/init")
            copyfile(f"{os.path.dirname(__file__)}/../resources/{tmpl_file}", f"{td}/init/{tmpl_file}")

            result = sut.read_plugin_list(td)
            self.assertEqual(self.dummy_plugin_json, result)

    def test_build_request_body(self):
        result = sut.build_request_body(self.dummy_plugin_json)

        with open(os.path.dirname(__file__) + "/../resources/plugin_request.json", 'r') as f:
            dummy_request = f.read()

        expected_request_json = json.loads(dummy_request)
        self.assertEqual(expected_request_json, result)

    def test_call_wp_api_for_bad_response(self):
        dummy_request_body = {"dummy": "body"}
        response = mock({
            "status_code": 500,
            "text": "TEST Error",
            "content": "TEST Error 500",
            "reason": "Internal Server Error"
        }, spec=requests.Response)
        when(requests).post(ANY(str), data=ANY(), headers=ANY()).thenReturn(response)

        with self.assertRaises(RuntimeError):
            sut.call_wp_api(dummy_request_body)

    def test_call_wp_api(self):
        with open(os.path.dirname(__file__) + "/../resources/plugin_request.json", 'r') as f:
            dummy_request_body = f.read()
        with open(os.path.dirname(__file__) + "/../resources/plugin_request_encoded.txt", 'r') as f:
            dummy_request_body_enc = f.read()
        with open(os.path.dirname(__file__) + "/../resources/plugin_response.json", 'r') as f:
            dummy_response_body = f.read()
        response = mock({"status_code": 200, "text": dummy_response_body}, spec=requests.Response)
        dummy_request_json = json.loads(dummy_request_body)
        expected_url = "https://api.wordpress.org/plugins/update-check/1.1/"
        expected_data = f"plugins={dummy_request_body_enc}"
        expected_response = json.loads(dummy_response_body)
        when(requests).post(ANY(str), data=ANY(), headers=ANY()).thenReturn(response)

        result = sut.call_wp_api(dummy_request_json)
        self.assertEqual(expected_response, result)

        verify(requests, times=1).post(expected_url, data=expected_data,
            headers={"content-type": "application/x-www-form-urlencoded", "user-agent": "curl/7.71.1"})

    def test_is_update_plugins(self):
        self.assertFalse(sut.is_update_plugins({"plugins": []}))
        self.assertTrue(sut.is_update_plugins({"plugins": {"dummy/dummy.php": {"id": "NARF", "new_version": "42"}}}))

    def test_update_plugin_list(self):
        with open(os.path.dirname(__file__) + "/../resources/plugin_response.json", 'r') as f:
            dummy_response_body = f.read()
        dummy_plugin_status = json.loads(dummy_response_body)
        expected_result = self._create_updated_dummy_plugin_json()

        result = sut.update_plugin_list(self.dummy_plugin_json, dummy_plugin_status)
        self.assertEqual(expected_result, result)

    def test_write_plugin_list(self):
        with TemporaryDirectory("dummy-repo") as td:
            tmpl_file = "plugin-list.json"
            os.mkdir(f"{td}/init")
            copyfile(f"{os.path.dirname(__file__)}/../resources/{tmpl_file}", f"{td}/init/{tmpl_file}")

            dummy_plugin_list = self._create_updated_dummy_plugin_json()
            sut.write_plugin_list(td, dummy_plugin_list)

            with open(f"{td}/init/{tmpl_file}", 'r') as f:
                result = f.read()

            self.assertEqual(json.dumps(dummy_plugin_list, indent=2), result)

    @staticmethod
    def _create_dummy_plugin_json():
        return {
          "plugins": [
            {
              "download": "https://downloads.wordpress.org/plugin/classic-editor.1.5.zip",
              "version": "1.5",
              "key": "classic-editor/classic-editor.php"
            },
            {
              "download": "https://downloads.wordpress.org/plugin/cookie-notice.1.3.2.zip",
              "version": "1.3.2",
              "key": "cookie-notice/cookie-notice.php"
            }
          ]
        }

    @staticmethod
    def _create_updated_dummy_plugin_json():
        return {
          "plugins": [
            {
              "download": "https://downloads.wordpress.org/plugin/classic-editor.1.6.zip",
              "version": "1.6",
              "key": "classic-editor/classic-editor.php"
            },
            {
              "download": "https://downloads.wordpress.org/plugin/cookie-notice.1.3.2.zip",
              "version": "1.3.2",
              "key": "cookie-notice/cookie-notice.php"
            }
          ]
        }


if __name__ == '__main__':
    unittest.main()
