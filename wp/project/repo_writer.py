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

from jinja2 import Environment, FileSystemLoader


class RepoWriter(object):

    def __init__(self, repo_path):
        self.repo_path = repo_path

    def update_wp_version(self, version):
        env = Environment(loader=FileSystemLoader(self.repo_path), keep_trailing_newline=True)
        template = env.get_template("azure-pipelines.yml.template")
        data = template.render(wp_version=version)

        with open(self.repo_path + "/azure-pipelines.yml", "w") as pipeline_file:
            pipeline_file.write(data)
