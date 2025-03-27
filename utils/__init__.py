from rich.table import Table


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
