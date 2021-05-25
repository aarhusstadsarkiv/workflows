## SAM Workflows
This repository contains the future replacements for the current SAM workflow BAT files. The presentation layer is Gooey in advanced mode with each workflow visible as an option in the sidebar.


## Development
Call like so when testing the cli without Gooey:
```bash
python main.py accessfiles ../tests/test_export.csv C:/Users/azkb075/Downloads/test_result.csv --overwrite --local --dryrun --plain --ignore-gooey
```
