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
from shutil import copyfile
from tempfile import TemporaryDirectory
from wp.project.repo_writer import RepoWriter


class RepoWriterTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.maxDiff = None

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)

    def test_update_wp_version(self):
        dummy_version = "42"

        with open(os.path.dirname(__file__) + "/../resources/azure-pipelines.yml.expected", 'r') as f:
            expected_result = f.read()

        with TemporaryDirectory("dummy-repo") as td:
            tmpl_file = "azure-pipelines.yml.template"
            copyfile(f"{os.path.dirname(__file__)}/../resources/{tmpl_file}", f"{td}/{tmpl_file}")

            sut = RepoWriter(td)
            sut.update_wp_version(dummy_version)

            with open(td + "/azure-pipelines.yml", 'r') as f:
                result = f.read()

            self.assertEqual(expected_result, result)


if __name__ == '__main__':
    unittest.main()
