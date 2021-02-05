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
import time
from mockito import when, mock, unstub, ANY, verify, verifyZeroInteractions

from wp import app
from wp.git.repository_fetcher import RepositoryFetcher
from wp import repos
from wp.project import docker_hub as dh
from wp.project import updater
from wp.pipeline import pipeline_interaction as pipe
from wp.pipeline import release_pipeline_interaction as rpi


class AppTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.orig_repos = repos.to_check
        self.dummy_latest_version = "5.4.2"
        self.dummy_init_repo_path = "/data/DUS/infra-docker-contentengine"
        self.dummy_img_repo_path = "/data/DUS/infra-docker-contentengine-img"
        self.dummy_repo = {
            "img-repo": "https://user@dev.azure.com/organization/PRJ/_git/infra-docker-dummy-img",
            "update-pipeline": "infra-docker-dummy",
            "build-init-pipeline": "wp-cloud-init",
            "build-img-pipeline": "wp-cloud-img",
            "rollout-pipeline": "Rollout Wordpress Image",
            "project": "PRJ"
        }

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        repos.to_check = self.orig_repos
        unstub()

    def test_process_repository(self):
        when(RepositoryFetcher).clone_or_update_repo().thenReturn(self.dummy_img_repo_path)
        when(RepositoryFetcher).cleanup()
        when(app).process_img_repo(ANY(), ANY(), ANY())

        result = app.process_repository(self.dummy_repo, "dummy_repo", self.dummy_latest_version)
        self.assertEqual(0, result)

        verify(RepositoryFetcher, times=1).clone_or_update_repo()
        verify(RepositoryFetcher, times=1).cleanup()
        verify(app, times=1).process_img_repo(self.dummy_repo, self.dummy_img_repo_path, self.dummy_latest_version)

    def test_process_img_repo(self):
        dummy_release_details = {"id": 21, "name": "update pipeline"}
        when(updater).compare_and_update(ANY(), ANY()).thenReturn(True)
        when(app).wait_for_build(ANY(), ANY())
        dummy_pipeline = mock(rpi.ReleasePipeline)
        when(rpi).ReleasePipeline(ANY(), ANY()).thenReturn(dummy_pipeline)
        when(dummy_pipeline).validate().thenReturn(dummy_release_details)
        when(dummy_pipeline).trigger_release(ANY())

        app.process_img_repo(self.dummy_repo, self.dummy_img_repo_path, self.dummy_latest_version)

        verify(updater, times=1).compare_and_update(self.dummy_img_repo_path, self.dummy_latest_version)
        verify(app, times=1).wait_for_build(self.dummy_repo["project"], self.dummy_repo["build-img-pipeline"])
        verify(rpi, times=1).ReleasePipeline(self.dummy_repo["project"], self.dummy_repo["update-pipeline"])
        verify(rpi, times=1).ReleasePipeline(self.dummy_repo["project"], self.dummy_repo["rollout-pipeline"])
        verify(dummy_pipeline, times=2).validate()
        verify(dummy_pipeline, times=2).trigger_release(21)

    def test_process_img_repo_for_no_update_required(self):
        when(updater).compare_and_update(ANY(), ANY()).thenReturn(False)
        when(app).wait_for_build(ANY(), ANY())
        when(rpi.ReleasePipeline)
        when(pipe.Pipeline)

        app.process_img_repo(self.dummy_repo, self.dummy_img_repo_path, self.dummy_latest_version)

        verify(updater, times=1).compare_and_update(self.dummy_img_repo_path, self.dummy_latest_version)
        verify(app, times=0).wait_for_build(ANY(), ANY())
        verifyZeroInteractions(rpi.ReleasePipeline, pipe.Pipeline)

    def test_determine_latest_version(self):
        expected_image_name = "wordpress"
        expected_filter = r"[0-9]+\.[0-9]+\.[0-9]-apache"
        expected_result = "5.4.2"
        dummy_tags = {"narf": "dummy tags"}
        dummy_filtered_tags = {"zort": "filtered tags"}
        dummy_highest_version = "5.4.2-apache"

        when(dh).fetch_tags(ANY()).thenReturn(dummy_tags)
        when(dh).filter_tags_regex(ANY(), ANY()).thenReturn(dummy_filtered_tags)
        when(dh).determine_highest_version(ANY()).thenReturn(dummy_highest_version)

        result = app.determine_latest_version()
        self.assertIsNotNone(result)
        self.assertEqual(expected_result, result)

        verify(dh, times=1).fetch_tags(expected_image_name)
        verify(dh, times=1).filter_tags_regex(dummy_tags, expected_filter)
        verify(dh, times=1).determine_highest_version(dummy_filtered_tags)

    def test_wait_for_build_with_error(self):
        dummy_build_result = "error"
        dummy_pipeline_name = "wp-docker-init"
        dummy_project = "PRJ"
        when(time).sleep(ANY())
        when(pipe.Pipeline).wait_for_build_pipeline().thenReturn(dummy_build_result)

        with self.assertRaises(Exception):
            app.wait_for_build(dummy_project, dummy_pipeline_name)

        verify(time, times=1).sleep(5)
        verify(pipe.Pipeline, times=1).wait_for_build_pipeline()

    def test_main(self):
        repos.to_check = self._dummy_repos()
        dummy_latest_version = "5.4.2"
        when(app).determine_latest_version().thenReturn(dummy_latest_version)
        when(app).process_repository(ANY(), ANY(), ANY()).thenReturn(0)

        app.main()

        verify(app, times=1).determine_latest_version()
        verify(app, times=3).process_repository(ANY(), ANY(), dummy_latest_version)

    @staticmethod
    def _dummy_repos():
        return {
            "dummy_repo1": {
                "img-repo": "https://user@dev.azure.com/organization/PRJ/_git/infra-docker-dummy-img",
                "acr": "orgprj",
                "update-pipeline": "infra-docker-dummy",
                "project": "PRJ"
            },
            "dummy_repo2": {
                "img-repo": "https://user@dev.azure.com/organization/PRJ/_git/infra-docker-dummy2-img",
                "acr": "orgprj",
                "update-pipeline": "infra-docker-dummy2",
                "project": "PRJ"
            },
            "dummy_repo3": {
                "img-repo": "https://user@dev.azure.com/organization/PRJ/_git/infra-docker-dummy3-img",
                "acr": "orgprj",
                "update-pipeline": "infra-docker-dummy3",
                "project": "PRJ"
            }}


if __name__ == '__main__':
    unittest.main()
