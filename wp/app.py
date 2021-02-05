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

import sys
import time
import traceback
from wp import repos
from wp.git.repository_fetcher import RepositoryFetcher
from wp.project import docker_hub as dh
from wp.project import updater
from wp.pipeline import pipeline_interaction as pipe
from wp.pipeline import release_pipeline_interaction as rpi


def process_repository(repo, key, latest_version):
    git_repo_img = RepositoryFetcher(repo["img-repo"], f"{key}_img")

    try:
        img_repo_path = git_repo_img.clone_or_update_repo()
        process_img_repo(repo, img_repo_path, latest_version)
        return 0
    except (Exception, FileNotFoundError) as e:
        print(f"Unable to process repository: {repo}")
        print(f"{e}\nCaused by: {traceback.format_exc()}")
        return 1
    finally:
        git_repo_img.cleanup()


def process_img_repo(repo, img_repo_path, latest_version):
    updated = updater.compare_and_update(img_repo_path, latest_version)
    if updated:
        wait_for_build(repo["project"], repo["build-img-pipeline"])
        trigger_database_update(repo)
        trigger_image_rollout(repo)


def trigger_database_update(repo):
    pipeline = rpi.ReleasePipeline(repo["project"], repo["update-pipeline"])
    details = pipeline.validate()
    pipeline.trigger_release(details["id"])


def trigger_image_rollout(repo):
    pipeline = rpi.ReleasePipeline(repo["project"], repo["rollout-pipeline"])
    details = pipeline.validate()
    pipeline.trigger_release(details["id"])


def wait_for_build(project, pipeline_name):
    print("wait for pipeline to start...")
    time.sleep(5)  # give the previous git-commit time to trigger the pipeline
    pipeline = pipe.Pipeline(project, pipeline_name)
    build_result = pipeline.wait_for_build_pipeline()
    if build_result != "succeeded":
        raise Exception(f"Build-Pipeline FAILED with result: {build_result}")


def determine_latest_version():
    tags = dh.fetch_tags("wordpress")
    filtered_tags = dh.filter_tags_regex(tags, r"[0-9]+\.[0-9]+\.[0-9]-apache")
    print(f"matching tags: {filtered_tags}")
    highest_version = dh.determine_highest_version(filtered_tags)

    return dh.filter_version_name(highest_version.rsplit("-")[0])


def main():
    print("Determine latest Wordpress-Version...")
    latest_version = determine_latest_version()
    occurred_errors = 0

    print(f"Found latest version: {latest_version}")
    print("Checking Wordpress-Repos...")
    for key, repo in repos.to_check.items():
        occurred_errors += process_repository(repo, key, latest_version)

    if occurred_errors > 0:
        sys.exit(f"Unable to process repositories! Encountered {occurred_errors} Errors! CHECK LOG!")


if __name__ == '__main__':
    main()
