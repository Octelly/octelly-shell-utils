from rich import print
from rich.progress import track, Progress, SpinnerColumn, TextColumn
import rich.markup
import typer
from typing_extensions import Annotated
from typing import List
from pathlib import Path
import shutil
import subprocess
import survey
import tomllib

state = {}

app = typer.Typer()


def get_project_root(start_dir: Path = Path.cwd()) -> Path:
    """
    Get Packwiz project root
    """

    assert start_dir.absolute()
    assert start_dir.is_dir(), "start_dir must be a directory"

    current_dir = start_dir

    while True:
        if "pack.toml" in [x.name for x in current_dir.iterdir() if x.is_file()]:
            return current_dir

        if len(current_dir.parents) > 0:
            current_dir = current_dir.parent
        else:
            raise RuntimeError("not a Packwiz project")


def packwiz(args: List[str]):
    """
    Run a Packwiz command in project root
    """

    print("[bold]Running:[/bold] packwiz {args}".format(args=" ".join(args)))

    process = subprocess.run([state["exec"]] + args, cwd=state["project_root"])

    if process.returncode == 0:
        print("[green]Packwiz command ran successfully![/green]")
    else:
        print(
            "[red]Packwiz command exitted with code {}[/red]".format(process.returncode)
        )
        raise typer.Exit()

    return process


def guess_packwiz_path() -> Path:
    """
    Guess the path to the Packwiz binary
    """
    path = shutil.which("packwiz")
    if path != None:
        return Path(path)
    else:
        return Path("packwiz")


def get_project_files() -> List[Path]:
    """
    Get a list of all project files
    """

    file_paths = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Discovering files...")

        file_paths = sorted(
            [file for file in state["project_root"].glob("**/*.pw.toml")]
        )

    return file_paths


def format_project_files(files: List[Path], format_str: str = "{name}") -> List[str]:
    """
    A formatter for list of project files
    """
    result = []

    for file in track(
        files, description="Generating formatted list...", transient=True
    ):
        contents = tomllib.loads(file.read_text())
        result.append(
            format_str.format(
                name=contents.get("name") or file.name[:-8],
                side=contents.get("side") or "unknown",
                filename=file.name,
                directory=file.parent.relative_to(state["project_root"]),
                path=file.relative_to(state["project_root"]),
                absolute_directory=file.parent.absolute(),
                absolute_path=file.absolute(),
            )
        )

    return result


@app.command()
def remove():
    """
    An interactive TUI for removing external files (.pw.toml)
    """

    # collect files
    file_paths = get_project_files()
    assert len(file_paths) > 0, "no external files found"
    print("Found {} files".format(len(file_paths)))

    # prepare file namse
    file_names = format_project_files(file_paths, "{name} ({directory})")

    # ask for selection
    selection = survey.routines.basket(
        "Which files should be removed?", options=file_names
    )

    if len(selection) > 0:
        # doule check
        if typer.confirm("Delete {} files?".format(len(selection))):
            for index in track(
                selection, description="Deleting selected files...", transient=True
            ):
                print(
                    "[red]Deleting {name}[/red]".format(
                        name=file_names[index],
                    )
                )
                file_paths[index].unlink()
            packwiz(["refresh"])
        else:
            print("[yellow]Aborted![/yellow]")

    print("[green]All done![/green]")


@app.command()
def repair():
    """
    Tries to repair a Packwiz project

    Currently takes the following steps:
    - deletes and re-creates the index.toml file
    """

    index_path = state["project_root"] / "index.toml"

    print("[yellow]Deleting and touching index.toml![/yellow]")
    index_path.unlink(missing_ok=True)
    index_path.touch()

    packwiz(["refresh"])


@app.command("list")
def file_list(
    list_format: Annotated[
        str,
        typer.Argument(
            envvar="PACKWIZ_LIST_FORMAT",
            help="Format with Python's formatting syntax",
        ),
    ] = "{name}"
):
    """
    List project files
    """

    print(
        rich.markup.escape(
            "\n".join(format_project_files(get_project_files(), list_format))
        )
    )


@app.callback()
def command(
    exec: Annotated[
        Path,
        typer.Option(
            envvar="PACKWIZ_EXEC",
            help="Specify the path of the Packwiz executable, searches in PATH otherwise",
            default_factory=guess_packwiz_path,
        ),
    ],
    path: Annotated[
        Path,
        typer.Option(
            envvar="PACKWIZ_PROJECT",
            help="Specify the path of the Packwiz project, defaults to CWD",
            default_factory=Path.cwd,
        ),
    ],
):
    """
    Utilities for working with the Packwiz modpack manager
    """

    state["exec"] = exec
    try:
        state["project_root"] = get_project_root(path)
    except RuntimeError:
        print(
            "{} [red]is not the root or a subdirectory of a Packwiz project[/red]".format(
                path
            )
        )
        raise typer.Exit(1)
