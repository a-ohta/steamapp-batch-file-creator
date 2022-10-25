# Create Batch (BAT) files to launch Steam app

```powershell
> python -m pipenv run python main.py --help
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  apps       Create steamapps bat files.
  shortcuts  Create non steamapps bat files.
> python -m pipenv run python main.py apps --help
Usage: main.py apps [OPTIONS]

  Create steamapps bat files.

Options:
  -d, --dir TEXT  steamapps dir path  [required]
  -o, --out TEXT  output dir
  --help          Show this message and exit.

> python -m pipenv run python main.py shortcuts --help
Usage: main.py shortcuts [OPTIONS]

  Create non steamapps bat files.

Options:
  -f, --file TEXT  steam shortcut vdf file path  [required]
  -o, --out TEXT   output dir
  --help           Show this message and exit.
```

## Attribution

Based on code originally posted to GitHub by scottrice
<https://github.com/scottrice/pysteam>
