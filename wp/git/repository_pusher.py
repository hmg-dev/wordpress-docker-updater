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
import subprocess
from wp.git.repository_fetcher import RepositoryFetcher
from wp.git.exceptions import RepositoryException


class RepositoryPusher(object):

    def __init__(self, repo_path):
        os.putenv("GIT_ASKPASS", RepositoryFetcher.GIT_HELPER)
        self.repo_path = repo_path

    def commit_and_push(self, message):
        cmd = f"cd {self.repo_path} && git add --all && git commit -m '{message}'"
        push_cmd = f"cd {self.repo_path} && git push"

        print("commit changes...")
        self._invoke(cmd)

        print("push changes...")
        self._invoke(push_cmd)

    @staticmethod
    def _invoke(cmd):
        p = subprocess.run(cmd, capture_output=True, encoding="UTF-8", shell=True)
        print(p.stdout)
        if p.returncode >= 1:
            raise RepositoryException(p.stderr)
