# sahityamigrate

[![Release](https://img.shields.io/github/v/release/srikanthsubra/sahityamigrate)](https://img.shields.io/github/v/release/srikanthsubra/sahityamigrate)
[![Build status](https://img.shields.io/github/actions/workflow/status/srikanthsubra/sahityamigrate/main.yml?branch=main)](https://github.com/srikanthsubra/sahityamigrate/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/srikanthsubra/sahityamigrate/branch/main/graph/badge.svg)](https://codecov.io/gh/srikanthsubra/sahityamigrate)
[![Commit activity](https://img.shields.io/github/commit-activity/m/srikanthsubra/sahityamigrate)](https://img.shields.io/github/commit-activity/m/srikanthsubra/sahityamigrate)
[![License](https://img.shields.io/github/license/srikanthsubra/sahityamigrate)](https://img.shields.io/github/license/srikanthsubra/sahityamigrate)

Migrate lyrics from sahityam.net mediawiki to anupallavi.com hugo site.

- **Github repository**: <https://github.com/srikanthsubra/sahityamigrate/>
- **Documentation** <https://srikanthsubra.github.io/sahityamigrate/>

## Getting started with your project


### 2. Set Up Your Development Environment

Then, install the environment and the pre-commit hooks with

```bash
make install
```

This will also generate your `uv.lock` file

### 3. Run the pre-commit hooks

Initially, the CI/CD pipeline might be failing due to formatting issues. To resolve those run:

```bash
uv run pre-commit run -a
```

### 4. Commit the changes

Lastly, commit the changes made by the two steps above to your repository.

```bash
git add .
git commit -m 'Fix formatting issues'
git push origin main
```

You are now ready to start development on your project!
The CI/CD pipeline will be triggered when you open a pull request, merge to main, or when you create a new release.

For activating the automatic documentation with MkDocs, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/mkdocs/#enabling-the-documentation-on-github).
To enable the code coverage reports, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/codecov/).

## Releasing a new version
