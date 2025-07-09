import subprocess


def git_get_branches() -> list[str]:
    output = subprocess.run(["git", "branch"], capture_output=True)
    branches: str = output.stdout.decode("utf-8")
    trimmedBranches: list[str] = [
        f"{branch.strip().removeprefix('* ')}" for branch in branches.splitlines()
    ]
    for branch in branches.splitlines():
        if branch.startswith("* "):
            current_branch = branch.removeprefix("* ")
    return {"branches": trimmedBranches, "current": current_branch}


def git_checkout(branch: str):
    return subprocess.run(["git", "checkout", branch], capture_output=True)
