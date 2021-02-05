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

import unittest
from mockito import when, mock, unstub, ANY, verify, verifyZeroInteractions
from wp.project.repo_details import RepoDetails
from wp.project import repo_writer as repow
from wp.git import repository_pusher as repush
from wp.project import updater as sut
from wp.project import wp_plugins


class UpdaterTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.dummy_repo_path = "/tmp"
        self.dummy_latest_version = "42"
        self.dummy_repo_pusher = mock(repush.RepositoryPusher)

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        unstub()

    def test_update_wp_version(self):
        dummy_repo_writer = mock(repow.RepoWriter)
        when(repow).RepoWriter(ANY()).thenReturn(dummy_repo_writer)
        when(dummy_repo_writer).update_wp_version(ANY())

        sut.update_wp_version(self.dummy_repo_path, self.dummy_latest_version)

        verify(repow, times=1).RepoWriter(self.dummy_repo_path)
        verify(dummy_repo_writer, times=1).update_wp_version(self.dummy_latest_version)

    def test_check_and_update_plugins_for_no_update_required(self):
        dummy_plugin_json = {"plugin": "NARF"}
        dummy_request_body = {"request": "ZORT"}
        dummy_plugin_status = {"status": "POIT"}
        when(wp_plugins).read_plugin_list(ANY()).thenReturn(dummy_plugin_json)
        when(wp_plugins).build_request_body(ANY()).thenReturn(dummy_request_body)
        when(wp_plugins).call_wp_api(ANY()).thenReturn(dummy_plugin_status)
        when(wp_plugins).is_update_plugins(ANY()).thenReturn(False)
        when(wp_plugins).update_plugin_list(ANY(), ANY())
        when(wp_plugins).write_plugin_list(ANY(), ANY())

        result = sut.check_and_update_plugins(self.dummy_repo_path)
        self.assertFalse(result)

        verify(wp_plugins, times=1).read_plugin_list(self.dummy_repo_path)
        verify(wp_plugins, times=1).build_request_body(dummy_plugin_json)
        verify(wp_plugins, times=1).call_wp_api(dummy_request_body)
        verify(wp_plugins, times=1).is_update_plugins(dummy_plugin_status)
        verify(wp_plugins, times=0).update_plugin_list(ANY(), ANY())
        verify(wp_plugins, times=0).write_plugin_list(ANY(), ANY())

    def test_check_and_update_plugins(self):
        dummy_plugin_json = {"plugin": "NARF"}
        dummy_request_body = {"request": "ZORT"}
        dummy_plugin_status = {"status": "POIT"}
        dummy_plugin_updated_json = {"plugin": "update"}
        when(wp_plugins).read_plugin_list(ANY()).thenReturn(dummy_plugin_json)
        when(wp_plugins).build_request_body(ANY()).thenReturn(dummy_request_body)
        when(wp_plugins).call_wp_api(ANY()).thenReturn(dummy_plugin_status)
        when(wp_plugins).is_update_plugins(ANY()).thenReturn(True)
        when(wp_plugins).update_plugin_list(ANY(), ANY()).thenReturn(dummy_plugin_updated_json)
        when(wp_plugins).write_plugin_list(ANY(), ANY())

        result = sut.check_and_update_plugins(self.dummy_repo_path)
        self.assertTrue(result)

        verify(wp_plugins, times=1).read_plugin_list(self.dummy_repo_path)
        verify(wp_plugins, times=1).build_request_body(dummy_plugin_json)
        verify(wp_plugins, times=1).call_wp_api(dummy_request_body)
        verify(wp_plugins, times=1).is_update_plugins(dummy_plugin_status)
        verify(wp_plugins, times=1).update_plugin_list(dummy_plugin_json, dummy_plugin_status)
        verify(wp_plugins, times=1).write_plugin_list(self.dummy_repo_path, dummy_plugin_updated_json)

    def test_check_and_update_wp_for_no_update_required(self):
        dummy_repo_version = "21"
        dummy_latest_version = "21"

        when(RepoDetails).determine_imageversion(self.dummy_repo_path).thenReturn(dummy_repo_version)
        when(sut).update_wp_version(ANY(), ANY())

        result = sut.check_and_update_wp(self.dummy_repo_path, dummy_latest_version)
        self.assertFalse(result)

        verify(RepoDetails, times=1).determine_imageversion(self.dummy_repo_path)
        verify(sut, times=0).update_wp_version(ANY(), ANY())

    def test_check_and_update_wp(self):
        dummy_repo_version = "21"
        when(RepoDetails).determine_imageversion(self.dummy_repo_path).thenReturn(dummy_repo_version)
        when(sut).update_wp_version(ANY(), ANY())

        result = sut.check_and_update_wp(self.dummy_repo_path, self.dummy_latest_version)
        self.assertTrue(result)

        verify(RepoDetails, times=1).determine_imageversion(self.dummy_repo_path)
        verify(sut, times=1).update_wp_version(self.dummy_repo_path, self.dummy_latest_version)

    def test_compare_and_update_no_update(self):
        when(sut).check_and_update_wp(ANY(), ANY()).thenReturn(False)
        when(sut).check_and_update_plugins(ANY()).thenReturn(False)
        when(repush).RepositoryPusher(ANY())

        self.assertFalse(sut.compare_and_update(self.dummy_repo_path, "42"))

        verify(sut, times=1).check_and_update_wp(self.dummy_repo_path, self.dummy_latest_version)
        verify(sut, times=1).check_and_update_plugins(self.dummy_repo_path)
        verifyZeroInteractions(repush)

    def test_compare_and_update_no_plugins_update(self):
        when(sut).check_and_update_wp(ANY(), ANY()).thenReturn(True)
        when(sut).check_and_update_plugins(ANY()).thenReturn(False)
        when(repush).RepositoryPusher(ANY()).thenReturn(self.dummy_repo_pusher)
        when(self.dummy_repo_pusher).commit_and_push(ANY())
        expected_commit_msg = f"auto-update wordpress: wp-version={True} | plugins={False}"

        self.assertTrue(sut.compare_and_update(self.dummy_repo_path, "42"))

        verify(sut, times=1).check_and_update_wp(self.dummy_repo_path, self.dummy_latest_version)
        verify(sut, times=1).check_and_update_plugins(self.dummy_repo_path)
        verify(repush, times=1).RepositoryPusher(self.dummy_repo_path)
        verify(self.dummy_repo_pusher, times=1).commit_and_push(expected_commit_msg)

    def test_compare_and_update_no_wp_update(self):
        when(sut).check_and_update_wp(ANY(), ANY()).thenReturn(False)
        when(sut).check_and_update_plugins(ANY()).thenReturn(True)
        when(repush).RepositoryPusher(ANY()).thenReturn(self.dummy_repo_pusher)
        when(self.dummy_repo_pusher).commit_and_push(ANY())
        expected_commit_msg = f"auto-update wordpress: wp-version={False} | plugins={True}"

        self.assertTrue(sut.compare_and_update(self.dummy_repo_path, "42"))

        verify(sut, times=1).check_and_update_wp(self.dummy_repo_path, self.dummy_latest_version)
        verify(sut, times=1).check_and_update_plugins(self.dummy_repo_path)
        verify(repush, times=1).RepositoryPusher(self.dummy_repo_path)
        verify(self.dummy_repo_pusher, times=1).commit_and_push(expected_commit_msg)

    def test_compare_and_update_full_update(self):
        when(sut).check_and_update_wp(ANY(), ANY()).thenReturn(True)
        when(sut).check_and_update_plugins(ANY()).thenReturn(True)
        when(repush).RepositoryPusher(ANY()).thenReturn(self.dummy_repo_pusher)
        when(self.dummy_repo_pusher).commit_and_push(ANY())
        expected_commit_msg = f"auto-update wordpress: wp-version={True} | plugins={True}"

        self.assertTrue(sut.compare_and_update(self.dummy_repo_path, "42"))

        verify(sut, times=1).check_and_update_wp(self.dummy_repo_path, self.dummy_latest_version)
        verify(sut, times=1).check_and_update_plugins(self.dummy_repo_path)
        verify(repush, times=1).RepositoryPusher(self.dummy_repo_path)
        verify(self.dummy_repo_pusher, times=1).commit_and_push(expected_commit_msg)


if __name__ == '__main__':
    unittest.main()
