import json
import os
import subprocess

import typer
from rich import print as rich_print


def sfdx_check_sf_project():
    """
    Check if the root directory is a Salesforce project.
    """
    typer.secho("Checking if this is a Salesforce project...", fg="yellow", nl=False)
    if not os.path.exists("sfdx-project.json"):
        typer.secho("This is not a Salesforce project.", fg="yellow")
        raise typer.Exit(code=1)
    rich_print(":white_check_mark:")


def sfdx_check_sf_cli_installed():
    """
    Check if the Salesforce CLI is installed.
    """
    typer.secho("Checking if the Salesforce CLI is installed...", fg="yellow", nl=False)
    try:
        subprocess.run(
            ["sf", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        rich_print(":white_check_mark:")
    except FileNotFoundError:
        typer.echo()
        typer.secho("The Salesforce CLI is not installed.", fg="yellow")
        raise typer.Exit(code=1)


def sfdx_check_sgd_plugin_installed():
    """
    Check if the sfdx-git-delta plugin is installed.
    """
    typer.secho(
        "Checking if the sfdx-git-delta plugin is installed...", fg="yellow", nl=False
    )

    plugins = subprocess.run(
        ["sf", "plugins", "--json"],
        capture_output=True,
    )

    plugins_dict = json.loads(plugins.stdout.decode("utf-8"))

    for plugin in plugins_dict:
        if plugin.get("options").get("name") == "sfdx-git-delta":
            rich_print(":white_check_mark:")
            return

    typer.secho("The sfdx-git-delta plugin is not installed.", fg="yellow")
    typer.secho(
        'Please install it by running "sf plugins install sfdx-git-delta"',
        fg="yellow",
    )
    raise typer.Exit(code=1)


def sfdx_sgd(from_branch: str, to_branch: str = None):
    """
    Run the Salesforce CLI command 'sf sgd source delta --from <source> --json'.
    """
    params = ["sf", "sgd", "source", "delta", "--json", "--from", f"{from_branch}"]
    if to_branch:
        params.extend(["--to", f"{to_branch}"])
    return subprocess.run(
        params,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def sfdx_get_orgs() -> list[str]:
    output = subprocess.run(["sf", "org", "list", "--json"], capture_output=True)
    orgs: str = output.stdout.decode("utf-8")
    orgs = json.loads(orgs).get("result").get("nonScratchOrgs")
    return [org.get("alias") for org in orgs]


def sfdx_deploy(
    manifest_file_path: str,
    org: str,
    validate_only: bool = False,
    test_level: str = "NoTestRun",
):
    """
    Run the Salesforce CLI command 'sf project deploy'.
    """
    params = [
        "sf",
        "project",
        "deploy",
        "start",
        "-x",
        manifest_file_path,
        "-o",
        org,
        "-l",
        test_level,
        "--json",
    ]

    if validate_only:
        params.extend(["--dry-run"])

    return subprocess.run(
        params,
        capture_output=True,
    )


def sfdx_quick_deploy(job_id: str, org: str):
    """
    Run the Salesforce CLI command 'sf project deploy'.
    """
    params = [
        "sf",
        "project",
        "deploy",
        "quick",
        "-o",
        org,
        "--job-id",
        job_id,
        "--json",
    ]

    return subprocess.run(
        params,
        capture_output=True,
    )
