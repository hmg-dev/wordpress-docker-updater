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
import requests
import urllib.parse


def read_plugin_list(repository_dir):
    with open(f"{repository_dir}/init/plugin-list.json", 'r') as f:
        plugin_list = f.read()

    return json.loads(plugin_list)


def build_request_body(plugin_json):
    request_body = {"plugins": {}}

    for p in plugin_json["plugins"]:
        request_body["plugins"].update({p["key"]: {"Version": p["version"]}})

    return request_body


def call_wp_api(request_body):
    url = "https://api.wordpress.org/plugins/update-check/1.1/"
    post_data = f"plugins={urllib.parse.quote(json.dumps(request_body), safe='')}"
    print(f"request to: {url}")
    print(f"POST-data: {post_data}")
    response = requests.post(url, data=post_data,
                             headers={"content-type": "application/x-www-form-urlencoded", "user-agent": "curl/7.71.1"})

    if response.status_code != 200:
        print(f"Got Response: {response.content}")
        raise RuntimeError(f"Request to '{url}' failed! Got status code: {response.status_code} - {response.reason}")

    return json.loads(response.text)


def is_update_plugins(plugin_status):
    return len(plugin_status["plugins"]) > 0


def update_plugin_list(plugin_list, plugin_status):
    plugin_list_update = plugin_list
    for key in plugin_status["plugins"]:
        for p in plugin_list_update["plugins"]:
            if p["key"] == key:
                value = plugin_status["plugins"][key]
                p["version"] = value["new_version"]
                p["download"] = value["package"]

    return plugin_list_update


def write_plugin_list(repository_dir, plugin_list):
    with open(f"{repository_dir}/init/plugin-list.json", "w") as plj:
        plj.write(json.dumps(plugin_list, indent=2))
