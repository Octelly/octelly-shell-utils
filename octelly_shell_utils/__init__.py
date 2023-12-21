import typer

app = typer.Typer()

from .utils import utils

for name, entry in utils.items():
    app.add_typer(entry, name=name)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Octelly's shell utilities
    """
    if ctx.invoked_subcommand is None:
        print(":)")
        for name, entry in utils.items():
            print(entry.info.help)
