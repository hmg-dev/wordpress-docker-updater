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
import re
import requests
from packaging.version import parse


def fetch_tags(image_name):
    url = _build_request_uri(image_name)

    print(f"request to: {url}")
    response = requests.get(url)

    if response.status_code != 200:
        raise RuntimeError(f"Request to '{url}' failed! Got status code: {response.status_code}")

    return json.loads(response.text)


def _build_request_uri(image_name):
    path = image_name
    if "/" not in image_name:
        path = "library/" + image_name

    # only fetches the latest 100 tags! default seems to be 10 now -.-
    # 100 is the maximum for parameter page_size
    # in order to fetch more tags, its necessary to do multiple requests with the parameter "page"
    # but the last 100 tags should be enough for our requirements ...hopefully!
    return f"https://hub.docker.com/v2/repositories/{path}/tags?page_size=100"


def filter_tags(tags, name_filter):
    filtered_tags = [x for x in tags["results"] if name_filter in x['name']]
    return filtered_tags


def filter_tags_regex(tags, name_filter):
    filtered_tags = [x for x in tags["results"] if re.search(name_filter, x['name']) is not None]
    return filtered_tags


def determine_highest_version(tags):
    highest_version = None
    highest_version_name = None
    for t in tags:
        current_version = parse(t["name"])
        if highest_version is None or highest_version < current_version:
            highest_version = current_version
            highest_version_name = t["name"]

    return highest_version_name


##
# if patch-version is "0", it's not reflected in the download-links!
# so we have to remove it.
def filter_version_name(original_version):
    match = re.search(r"([0-9]\.[0-9])\.0", original_version)
    if match is not None:
        return match.group(1)

    return original_version
