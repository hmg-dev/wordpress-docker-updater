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
import shutil
from pathlib import Path
from wp import config as conf
from wp.git.exceptions import RepositoryException


class RepositoryFetcher(object):
    GIT_HELPER = os.path.dirname(__file__) + "/../../git-passwd-helper.sh"

    def __init__(self, url, name):
        os.putenv("GIT_ASKPASS", RepositoryFetcher.GIT_HELPER)
        self.url = url
        self.name = name

    def clone_repo(self):
        print(f"fetching repository: {self.url}")
        cmd = f"cd {conf.workdir} && git clone {self.url} {self.name}"
        return self._invoke(cmd)

    def target_path(self):
        return conf.workdir + self.name

    def update_repo(self):
        print(f"updating repository: {self.target_path()}")
        cmd = f"cd {self.target_path()} && git pull --rebase"
        return self._invoke(cmd)

    def _invoke(self, cmd):
        p = subprocess.run(cmd, capture_output=True, encoding="UTF-8", shell=True)
        print(p.stdout)
        if p.returncode >= 1:
            raise RepositoryException(p.stderr)

        return self.target_path()

    def clone_or_update_repo(self):
        print(f"Check if {self.target_path()} is a valid git repo")
        git_path = Path(self.target_path(), ".git")
        if git_path.is_dir():
            return self.update_repo()

        return self.clone_repo()

    def cleanup(self):
        shutil.rmtree(self.target_path())
