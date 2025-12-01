<!-- markdownlint-disable MD001 -->
# Installation

This document explains how to install dependencies and set up the environment required to run the Hacker-News thread summarizer scripts.

Two common installation methods are shown below: using your system Python + pip and using the `uv` environment manager.

## 1) System Python + pip (recommended / widely supported)

- Make sure you have Python 3.10+ installed and that `python3` and `pip` are available on your PATH.
- Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate   # on macOS / Linux
# or on Windows (PowerShell): .\.venv\Scripts\Activate.ps1
```

- Upgrade pip and install requirements:

```bash
python -m ensurepip --upgrade   # ensures pip is available in some envs
python -m pip install --upgrade pip
pip install -r requirements.txt
```

- Optional (Jupyter/IPython kernel support):

```bash
pip install ipykernel
python -m ipykernel install --user --name=hn-thread-summarizer
```

This approach is compatible with VS Code, Jupyter and most CI systems.

## 2) Using `uv` (alternative environment manager)

`uv` creates lighter weight virtual environments using a different resolver and may not install `pip` by default. It is perfectly fine to use `uv`, but note some tooling (e.g., VS Code) expects `pip` to exist in the environment when installing packages like `ipykernel`.

If you prefer `uv`, install packages using `uv pip` and ensure pip is present for compatibility with other tools.

```bash
# create a uv environment
uv venv .venv-uv

# activate the uv-managed environment (same as any venv)
source .venv-uv/bin/activate          # macOS / Linux
# or on Windows (PowerShell)
# .\.venv-uv\Scripts\Activate.ps1

# make sure pip is present (recommended when using VS Code/Jupyter)
uv pip install pip

# install project dependencies
uv pip install -r requirements.txt

# install ipykernel so notebooks and VS Code can use the kernel
uv pip install ipykernel
python -m ipykernel install --user --name=hn-thread-summarizer-uv
```

Notes:
- If VS Code tries to auto-install missing packages it will use `pip`. Since `uv` manages packages via `uv pip`, installing `pip` in the uv environment ensures VS Code's automatic actions work.
- You can continue to use `uv` for package management (e.g. `uv pip install <pkg>`) after you've installed `pip` inside the environment.

## 3) Environment variables

Create a `.env` file at the project root or export environment variables in your shell:

```text
OPENAI_API_KEY="your_openai_api_key"
# (or) PERPLEXITY_API_KEY="your_perplexity_api_key"
```

Use `dotenv` or your shell environment so the scripts can pick up API keys.

## 4) Quick verification

After installation and activation you should be able to run a quick check that Python and the `requests` package are available:

```bash
# for older python versions (<3.12):
python -c "import sys, pkgutil; print('python', sys.version); print('requests:', pkgutil.find_loader('requests') is not None)"
# for newer python versions:
python -c "import sys, pkgutil, importlib; print('python', sys.version); print('requests:', importlib.util.find_spec('requests') is not None)"
```

That's it — you should now be able to run the scripts described in `USAGE.md`.

## 5) About the packages in requirements.txt

The `requirements.txt` file lists Python packages the project depends on (for example `pydantic`, `openai`, `tiktoken`, `requests`, etc.). A few notes about those packages and why you should prefer installing them into an isolated virtual environment rather than your system Python:

- Rapid development: libraries such as `pydantic` and `openai` evolve quickly and release breaking changes or new features frequently. Pinning versions in `requirements.txt` helps reproduction, but mixing versions in the system Python can cause hard-to-debug conflicts.
- Transitive dependencies: many libraries bring extra dependencies of their own. Installing many projects globally increases the risk of dependency clashes and can pollute your system Python's package set.
- Security & stability: keeping dependencies isolated to a virtual environment reduces the chance of accidentally changing system-wide packages that other applications rely upon (or require elevated privileges to modify).
- Tooling compatibility: editors, notebook kernels and CI systems expect a clean environment (and sometimes `pip` to be present). Installing into an environment makes it easier to manage tooling like `ipykernel`, `pytest`, or `pre-commit` without affecting the rest of your machine.

Recommendation: always create a dedicated virtual environment (`venv` or `uv`), activate it and then install the `requirements.txt` into that environment. That keeps things reproducible and prevents the project dependencies from polluting your system Python.
