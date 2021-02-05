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

import subprocess
import unittest
from mockito import mock, when, unstub, ANY, verify
from wp.git.repository_pusher import RepositoryPusher
from wp.git.exceptions import RepositoryException


class RepositoryPusherTest(unittest.TestCase):
    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        self.dummy_path = "/tmp/"
        self.process = mock({"returncode": 0, "stderr": "", "stdout": ""})
        self.sut = RepositoryPusher(self.dummy_path)

    def tearDown(self) -> None:
        unittest.TestCase.tearDown(self)
        unstub()

    def test_commit_and_push(self):
        dummy_msg = "update wp to version 42"
        expected_cmd = f"cd {self.dummy_path} && git add --all && git commit -m '{dummy_msg}'"
        expected_push_cmd = f"cd {self.dummy_path} && git push"
        when(subprocess).run(ANY(str), capture_output=True, encoding="UTF-8", shell=True).thenReturn(self.process)

        self.sut.commit_and_push(dummy_msg)
        verify(subprocess, times=1).run(expected_cmd, capture_output=True, encoding="UTF-8", shell=True)
        verify(subprocess, times=1).run(expected_push_cmd, capture_output=True, encoding="UTF-8", shell=True)

    def test_commit_and_push_for_error(self):
        dummy_msg = "update wp to version 42"
        expected_cmd = f"cd {self.dummy_path} && git add --all && git commit -m '{dummy_msg}'"
        expected_push_cmd = f"cd {self.dummy_path} && git push"
        self.process = mock({"returncode": 1, "stderr": "error cloning repo", "stdout": "TEST ERROR"})
        when(subprocess).run(ANY(str), capture_output=True, encoding="UTF-8", shell=True).thenReturn(self.process)

        with self.assertRaises(RepositoryException):
            self.sut.commit_and_push(dummy_msg)
        verify(subprocess, times=1).run(expected_cmd, capture_output=True, encoding="UTF-8", shell=True)
        verify(subprocess, times=0).run(expected_push_cmd, capture_output=True, encoding="UTF-8", shell=True)


if __name__ == '__main__':
    unittest.main()
