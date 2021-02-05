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
import subprocess
import shutil
from tempfile import TemporaryDirectory
from mockito import mock, when, unstub, ANY, verify
from wp.git.repository_fetcher import RepositoryFetcher
from wp.git.exceptions import RepositoryException
from wp import config as conf


class RepositoryFetcherTest(unittest.TestCase):

    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.dummy_url = "https://user@git.company.narf/dummy/repo.git"
        self.dummy_name = "dummy-repo"
        self.sut = RepositoryFetcher(self.dummy_url, self.dummy_name)
        self.conf_workdir = conf.workdir
        self.process = mock({"returncode": 0, "stderr": "", "stdout": ""})
        when(subprocess).run(ANY(str), capture_output=True, encoding='UTF-8', shell=True).thenReturn(self.process)

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        conf.workdir = self.conf_workdir
        unstub()

    def test_clone_repo(self):
        expected_cmd = f"cd {conf.workdir} && git clone {self.dummy_url} {self.dummy_name}"
        expected_target_path = conf.workdir + self.dummy_name

        result = self.sut.clone_repo()
        self.assertEqual(expected_target_path, result)
        verify(subprocess, times=1).run(expected_cmd, capture_output=True, encoding="UTF-8", shell=True)

    def test_clone_repo_for_error(self):
        expected_cmd = f"cd {conf.workdir} && git clone {self.dummy_url} {self.dummy_name}"
        dummy_output = "Cloning into 'infra-docker-dummy'..."
        self.process = mock({"returncode": 1, "stderr": "error cloning repo", "stdout": dummy_output})
        when(subprocess).run(ANY(str), capture_output=True, encoding="UTF-8", shell=True).thenReturn(self.process)

        self.assertRaises(RepositoryException, self.sut.clone_repo)
        verify(subprocess, times=1).run(expected_cmd, capture_output=True, encoding="UTF-8", shell=True)

    def test_update_repo(self):
        expected_target_path = conf.workdir + self.dummy_name
        expected_cmd = f"cd {expected_target_path} && git pull --rebase"

        result = self.sut.update_repo()
        self.assertEqual(expected_target_path, result)
        verify(subprocess, times=1).run(expected_cmd, capture_output=True, encoding="UTF-8", shell=True)

    def test_clone_or_update_repo_for_update(self):
        with TemporaryDirectory("dummy-repo") as td:
            os.makedirs(f"{td}/{self.dummy_name}/.git")
            conf.workdir = td + "/"

            expected_target_path = conf.workdir + self.dummy_name
            expected_cmd = f"cd {expected_target_path} && git pull --rebase"
            result = self.sut.clone_or_update_repo()

        self.assertEqual(expected_target_path, result)
        verify(subprocess, times=1).run(expected_cmd, capture_output=True, encoding="UTF-8", shell=True)

    def test_clone_or_update_repo_for_clone(self):
        conf.workdir = "/tmp/INVALID/"
        expected_cmd = f"cd {conf.workdir} && git clone {self.dummy_url} {self.dummy_name}"
        expected_target_path = conf.workdir + self.dummy_name

        result = self.sut.clone_or_update_repo()
        self.assertEqual(expected_target_path, result)
        verify(subprocess, times=1).run(expected_cmd, capture_output=True, encoding="UTF-8", shell=True)

    def test_cleanup(self):
        expected_target_path = conf.workdir + self.dummy_name
        when(shutil).rmtree(ANY())

        self.sut.cleanup()

        verify(shutil, times=1).rmtree(expected_target_path)


if __name__ == '__main__':
    unittest.main()
