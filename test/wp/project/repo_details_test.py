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

import os
import unittest
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory
from wp.project.repo_details import RepoDetails


class RepoDetailsTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.dummy_repo = {
            "name": "dummy-repo",
            "git": "https://user@dev.azure.com/handelsblattgroup/PRJ/_git/dummy-repo",
            "acr": "orgprj",
            "build_pipeline": "TODO"
        }
        self.dummy_path = "/tmp/dummy-repo"
        self.sut = RepoDetails(self.dummy_repo)

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)

    def test_determine_imageversion_for_missing_azurepipeline(self):
        expected_version = RepoDetails.DEFAULT_IMAGE_VERSION
        result = self.sut.determine_imageversion(self.dummy_path)
        self.assertEqual(expected_version, result)

    def test_determine_imageversion_for_valid_pipeline_file(self):
        expected_version = "3.7"
        with TemporaryDirectory("dummy-repo") as td:
            test_file = os.path.dirname(__file__) + "/../resources/azure-pipelines.yml"
            self.assertTrue(Path(test_file).is_file())
            copyfile(test_file, td + "/azure-pipelines.yml")
            result = self.sut.determine_imageversion(td)
            self.assertEqual(expected_version, result)

    def test_determine_parent_image(self):
        expected_parent = "ubuntu:18.04"
        with TemporaryDirectory("dummy-repo") as td:
            test_file = os.path.dirname(__file__) + "/../resources/Dockerfile"
            self.assertTrue(Path(test_file).is_file())
            os.makedirs(td + "/xyz123")  # ensure Dockerfile is also found in arbitrary subdirs
            copyfile(test_file, td + "/xyz123/Dockerfile")
            result = self.sut.determine_parent_image(td)
            self.assertEqual(expected_parent, result)


if __name__ == '__main__':
    unittest.main()
