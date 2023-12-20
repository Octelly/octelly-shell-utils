from rich import print
import typer

app = typer.Typer()

from . import packwiz

commands = {"packwiz": packwiz.app}

for name, subcommand in commands.items():
    app.add_typer(subcommand, name=name)

# @app.callback(invoke_without_command=True)
# def main(ctx: typer.Context):
#    """
#    Octelly's shell utilities
#    """
#    if ctx.invoked_subcommand is None:
#        print(':)')

if __name__ == "__main__":
    app()
