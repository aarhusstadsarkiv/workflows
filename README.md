## Workflows
This repository contains the future replacements for the current SAM workflow BAT files. The presentation layer is Gooey in advanced mode with each workflow visible as an option in the sidebar.

## Development
Call from root like so when testing the cli without Gooey:
```bash
python workflows/cli.py accessfiles ../tests/test_export.csv C:/Users/azkb075/Downloads/test_result.csv --overwrite --local --dryrun --plain --ignore-gooey
```

```bash
python workflows/cli.py search C:/Users/azkb075/Downloads/latest_oas_backup.csv C:/Users/azkb075/Downloads/idlist.csv --storage-id 91+00966-1 --ignore-gooey
```

## Use
Brug værktøjet som commandline værktøj (`--ignore-gooey`), og brug kun `accessfiles` subcommandoen:
`poetry run workflows accessfiles C:\Users\azkb075\Downloads\csvs\sam_export.csv C:\Users\azkb075\Downloads\csvs\sam_export_done.csv  --ignore-gooey`

## Kompilering
Virker ikke aktuelt!

`poetry run pyinstaller --onefile --windowed --name workflows .\workflows\cli.py`

Se eventuelt docs: https://aarhusstadsarkiv.github.io/acadocs/development/pyinstaller.html
