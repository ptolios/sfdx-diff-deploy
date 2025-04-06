import json
import os
from typing import Annotated
import typer
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich.console import Console
from rich.table import Table


from git_commands import git_checkout, git_get_branches
from sfdx_commands import (
    sfdx_check_sf_cli_installed,
    sfdx_check_sf_project,
    sfdx_check_sgd_plugin_installed,
    sfdx_deploy,
    sfdx_get_orgs,
    sfdx_sgd,
)
from utils import component_failures_table, metadata_table, parse_package


console = Console()
app = typer.Typer(no_args_is_help=True)


@app.command()
def check_sf_project():
    """
    Check if the root directory is a Salesforce project.
    """
    sfdx_check_sf_project()


@app.command()
def check_sf_cli():
    """
    Check if the Salesforce CLI is installed.
    """
    sfdx_check_sf_cli_installed()


@app.command()
def check_sgd():
    """
    Check if the sfdx-git-delta plugin is installed.
    """
    sfdx_check_sgd_plugin_installed()


@app.command()
def diff_deploy(
    target: Annotated[
        str, typer.Option(help="The target branch or commit sha to apply the diff to.")
    ] = None,
    source: Annotated[
        str, typer.Argument(help="The source branch or commit sha to diff from.")
    ] = None,
    generate_manifest_only: Annotated[
        bool,
        typer.Option(
            "--generate-only",
            "-g",
            help="Generate the manifest only, without deploying.",
        ),
    ] = False,
):
    """
    Deploy the diff metadata of two branches, to an org.
    """
    os.chdir("..")
    check_sf_project()
    check_sf_cli()
    check_sgd()

    branches_info: dict = git_get_branches()
    local_branches: list[str] = branches_info.get("branches")
    current_branch: str = branches_info.get("default")
    local_branches_without_selected: list[str] = local_branches.copy()

    if source is None:
        console.rule("Branch selection")
        source = inquirer.select(
            message="Select branch to get the diff from:",
            choices=local_branches,
            default=None,
        ).execute()

    local_branches_without_selected.remove(source)
    if target is None:
        target = inquirer.select(
            message="Select branch to apply the diff to:",
            choices=local_branches_without_selected,
            default=None,
        ).execute()

    with console.status("Generating source delta..."):
        sgd_response = sfdx_sgd(source, target)
    output: str = sgd_response.stdout.decode("utf-8")
    if sgd_response.returncode == 0:
        output_dir = json.loads(output).get("result").get("output-dir")
        typer.secho(f'Source delta generated at "{output_dir}"', fg=typer.colors.GREEN)
    else:
        typer.secho(
            "An error occurred while generating the source delta.",
            err=True,
            fg=typer.colors.YELLOW,
        )
        error = json.loads(output).get("result").get("error")
        console.log(error, style="blink red")
        raise typer.Exit()

    # --------------- Show diff metadata table ---------------
    choices: list[Choice] = [
        Choice(name="Yes, show me the table", value=True),
        Choice(name="No, thanks. I'll check the manifest(s) myself", value=False),
    ]
    show_metadata_table: bool = inquirer.select(
        message="Do you want to see the metadata that will be deployed?",
        choices=choices,
        default=True,
    ).execute()

    if show_metadata_table:
        table: Table = metadata_table(
            parse_package(os.path.join(output_dir, "package/package.xml"))
        )
        console.print(table)

    if generate_manifest_only:
        console.print(
            f'Manifests generated successfully in folder "{os.path.abspath(output_dir)}". \nNo deployment will be performed.',
            style="bold green",
        )
        raise typer.Exit()

    # --------------- Select org to deploy to ---------------
    console.rule("Org selection")
    selected_org = inquirer.select(
        message="Select an org to deploy to:",
        choices=sfdx_get_orgs(),
        default=None,
    ).execute()

    validate: bool = typer.confirm("Do you want to validate the deployment?")
    message: str = (
        f"{'Validating deployment' if validate else 'Deploying'} to org '{selected_org}'..."
    )

    if output_dir:
        typer.secho(f"Checking out source branch {source}...", fg=typer.colors.YELLOW)
        git_checkout(source)

        manifest_file: str = os.path.join(output_dir, "package/package.xml")
        with console.status(message):
            deploy = sfdx_deploy(manifest_file, selected_org, validate)
            deploy_result = json.loads(deploy.stdout.decode("utf-8"))
        if deploy.returncode == 0:
            typer.secho(
                f"{'Validation' if validate else 'Deployment'} successful!",
                fg=typer.colors.GREEN,
            )

            if validate and typer.confirm(
                "Do you want to continue with the deployment?"
            ):
                with console.status(f"Deploying to org {selected_org}..."):
                    quick_deploy = sfdx_deploy(manifest_file, selected_org, False)
                quick_deploy_result = json.loads(quick_deploy.stdout.decode("utf-8"))
                if quick_deploy.returncode == 0:
                    typer.secho("Deployment successful!", fg=typer.colors.GREEN)
                else:
                    typer.secho(quick_deploy_result)
                    typer.secho(
                        "An error occurred while deploying.",
                        err=True,
                        fg=typer.colors.RED,
                    )

        else:
            # pprint(deploy_result)
            typer.secho(
                "An error occurred while deploying.", err=True, fg=typer.colors.RED
            )
            component_failures: dict = (
                deploy_result.get("result").get("details").get("componentFailures")
            )
            table: Table = component_failures_table(component_failures)
            console.print(table)


if __name__ == "__main__":
    app()
