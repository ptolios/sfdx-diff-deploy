from rich.table import Table
import xmltodict


def build_table(title, headers: list[dict], rows: list[list]):
    """
    Create a table with the given title, headers, and rows.
    """
    table = Table(title=title)
    for header in headers:
        table.add_column(**header)
    for row in rows:
        table.add_row(*row)
    return table


def component_failures_table(component_failures):
    table = Table(title="Component Errors")

    table.add_column("Type")
    table.add_column("Name")
    table.add_column("Error Message")
    for component_failure in component_failures:
        table.add_row(
            component_failure.get("componentType"),
            component_failure.get("fullName"),
            component_failure.get("problem"),
        )

    return table


def metadata_table(diff_metadata):
    """
    Create a table for diff metadata.
    """

    return build_table(
        title="Diff Metadata",
        headers=[
            {"header": "Type", "style": "cyan", "header_style": "bold cyan"},
            {"header": "Name", "style": "cyan", "header_style": "bold cyan"},
        ],
        rows=[
            [metadata.get("type"), metadata.get("name")] for metadata in diff_metadata
        ],
    )


def parse_package(package):
    """
    Parse the package.xml file and return a dictionary.
    """
    with open(package, "r") as f:
        package_dict = xmltodict.parse(f.read())
    result = []
    if "Package" not in package_dict:
        raise ValueError("Invalid package.xml file")

    for metadata_type in package_dict.get("Package").get("types"):
        members = metadata_type.get("members")
        if isinstance(members, str):
            members = [members]
        for metadata in members:
            result.append(
                {
                    "type": metadata_type.get("name"),
                    "name": metadata,
                }
            )

    return result
