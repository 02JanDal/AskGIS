# AskGIS
<!--![tests](https://github.com/02JanDal/askgis/workflows/Tests/badge.svg)
[![codecov.io](https://codecov.io/github/02JanDal/askgis/coverage.svg?branch=main)](https://codecov.io/github/02JanDal/askgis?branch=main)
![release](https://github.com/02JanDal/askgis/workflows/Release/badge.svg)

[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)-->

This is a **proof-of-concept** of integrating GPT-3 via LangChain into QGIS, giving it access to interact with the data in the current project.

https://user-images.githubusercontent.com/3686998/235088099-60aa9c06-7198-45d0-9f1b-e6c1524d0c92.mp4

## Installation

There is currently no packaged plugin available, refeer to [Development](#Development) if you are interested in testing this plugin.

Note: You must install [LangChain](https://pypi.org/project/langchain/) and [OpenAI](https://pypi.org/project/openai/) manually using PIP.

## Architecture

This plugin uses the Agent infrastructure of LangChain in order to be able to "branch out" to various tools, for example to be able to calculate mathematical questions or, in this case more interestingly, query and interact with the QGIS project.

When working with the QGIS project this plugin generates a prompt consisting of Python code and asks the LLM (GPT-3) to complete a function that will give it the answer it needs to perform the action the user wants. This Python code is than executed (for this reason
you probably shouldn't use this for anything important) to produce a sort of AST (Abstract Syntax Tree), which is then executed to produce the result. Finally, this result is passed back to the agent which uses it to formulate a final response for the user.

```mermaid
flowchart TD
    User -->|Question| Agent
    Agent --> C{Tool selection}
    C -->|Question| Math[Math Tool]
    Math -->|Answer| Agent
    C -->|Request| GIS[GIS Tool]
    GIS -->|Response| Agent
    GIS -->|Uses| QGIS
    Agent -->|Answer| User
```

## Development

Refer to [development](docs/development.md) for developing this QGIS3 plugin.

## Future Ideas

* Being able to ask for things close to something else (usually a POI); "Select schools within 500m of the train station"
* Indexing layers containing text (likely using QGIS expressions to produce the content to be indexed) and being able to query that index

## License
This plugin is licenced with[GNU General Public License, version 3](https://www.gnu.org/licenses/gpl-3.0.html)


See [LICENSE](LICENSE) for more information.
