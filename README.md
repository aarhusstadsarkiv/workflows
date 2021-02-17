## SAM Workflows
This repository contains the future replacements for the current SAM workflow BAT files. The presentation layer is Gooey in advanced mode with each workflow visible as an option in the sidebar.


## Development
Call like so when testing the cli without Gooey:
```bash
python main.py sam_access data/sam_export.csv import_to_sam.csv --upload --overwrite --watermark --ignore-gooey
```
