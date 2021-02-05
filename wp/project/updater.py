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

from packaging.version import parse
from wp.project.repo_details import RepoDetails
from wp.project import repo_writer as repow
from wp.git import repository_pusher as repush
from wp.project import wp_plugins as plugins


def compare_and_update(repo_path, latest_version):
    updated_plugins = check_and_update_plugins(repo_path)
    updated_wp = check_and_update_wp(repo_path, latest_version)

    if updated_plugins or updated_wp:
        print(f"detected updates: plugins={updated_plugins}, wp={updated_wp} - push changes")
        push_changes(repo_path, updated_wp, updated_plugins)

    return updated_wp or updated_plugins


def push_changes(repo_path, updated_wp, updated_plugins):
    repo_pusher = repush.RepositoryPusher(repo_path)
    repo_pusher.commit_and_push(f"auto-update wordpress: wp-version={updated_wp} | plugins={updated_plugins}")


def check_and_update_wp(repo_path, latest_version):
    print(f"compare version for {repo_path}")
    wp_version = RepoDetails.determine_imageversion(repo_path)
    current_version = parse(wp_version)
    remote_version = parse(latest_version)

    print(f"wp update required: {current_version < remote_version}")
    if is_update_wp_version(current_version, remote_version):
        update_wp_version(repo_path, latest_version)

    return is_update_wp_version(current_version, remote_version)


def is_update_wp_version(current_version, remote_version):
    return current_version < remote_version


def update_wp_version(repo_path, latest_version):
    repo_writer = repow.RepoWriter(repo_path)
    repo_writer.update_wp_version(latest_version)


def check_and_update_plugins(repo_path):
    print("check for plugin-updates...")
    plugins_json = plugins.read_plugin_list(repo_path)
    plugin_request = plugins.build_request_body(plugins_json)
    plugin_status = plugins.call_wp_api(plugin_request)
    is_update = plugins.is_update_plugins(plugin_status)

    if is_update:
        plugins_json_update = plugins.update_plugin_list(plugins_json, plugin_status)
        plugins.write_plugin_list(repo_path, plugins_json_update)

    print(f"plugin-update required: {is_update}")
    return is_update
