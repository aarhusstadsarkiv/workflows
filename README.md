## SAM Workflows
This repository contains the future replacements for the current workflow-bat's. The presentation-layer is Gooey in advanced mode with each workflow visible as an option in the sidebare.

#### mypy.ini
In `mypy.ini`, the per module options should be changed to reflect your module name:
```ini
# Per module options
[mypy-YOUR_MODULE_NAME.*]
disallow_untyped_defs = True

```

#### GitHub Actions
This repository includes a simple GitHub Actions workflow that sets up `poetry` with caching and checks linting & types using `flake8`, `black`, and `mypy`.
It also includes the initial setup for testing and upload to [codecov](https://codecov.io/) as a commented block. This part of the workflow requires adding a [codecov token](https://docs.codecov.io/docs#section-getting-started) as a [GitHub secret](https://help.github.com/en/actions/configuring-and-managing-workflows/creating-and-storing-encrypted-secrets). In addition, the call to `pytest` must be updated with the relevant project name.
