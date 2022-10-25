from pathlib import Path

import click
import vdf

from shortcut import ShortcutsVDF
from steam_url import steam_URL

# C:\\Program Files (x86)\\Steam\\userdata\\<userid>\\config\\shortcuts.vdf
# C:\\Program Files (x86)\\Steam\\steamapps

template = '''@ECHO OFF
powershell.exe -command Start-Process "steam://rungameid/{app_id}"'''


@click.group()
def cli():
    pass

@cli.command()
@click.option("--file", "-f", required=True, help="steam shortcut vdf file path")
@click.option("--out", "-o", required=False, default=".", help="output dir")
def shortcuts(file: str, out: str):
    """Create non steamapps bat files."""
    with open(file, mode="rb") as f:
        vdf_bytes = f.read()
    shortcuts_vdf: ShortcutsVDF = vdf.binary_loads(vdf_bytes)
    shortcuts = shortcuts_vdf["shortcuts"]
    for _, shortcut in shortcuts.items():
        out_file_path = Path(out, f'{shortcut["AppName"]}.bat')
        with open(out_file_path, mode="w", newline="\r\n") as out_file:
            out_file.write(
                template.format(app_id=steam_URL(shortcut=shortcut))
            )


def get_name(manifest_file: Path):
    with manifest_file.open('r') as manifest:
        for line in manifest:
            if 'name' in line:
                return ' '.join(line.split()[1:]).replace('"', '')
    raise


def get_content(manifest_file: Path):
    app_id = manifest_file.stem.split('_')[1]
    return template.format(app_id=app_id)


@cli.command()
@click.option("--dir", "-d", required=True, help="steamapps dir path")
@click.option("--out", "-o", required=False, default=".", help="output dir")
def apps(dir:str, out: str):
    """Create steamapps bat files."""
    steamapps_dir = Path(dir)
    if not steamapps_dir.is_dir():
        return
    for file in steamapps_dir.iterdir():
        if not file.stem.startswith("appmanifest"):
            continue
        file_content = get_content(file)
        file_name = get_name(file)
        out_file = (Path(out) / Path(file_name)).with_suffix(".bat")
        with out_file.open('w') as f:
            f.write(file_content)


if __name__ == "__main__":
    cli()
