# SST Streamlit App (Auto-scaffold, v2)

This app explores and runs modules from **SST_Mathematical_Proof_Python** and adds a **Script Runner** with live logs.

## Quick start

```bash
python -m venv .venv && source .venv\Scripts\activate  
pip install -r requirements.txt
streamlit run app.py
```

## How it works

- Discover all `*.py` files and index their functions/classes.
- **Entrypoint Runner:** If a module has `st_app()`, `main()`, `app()`, etc., run it inline.
- **Script Runner (subprocess):** Run **any** `*.py` via `python -u <file>.py`, regardless of `main()`.
  - Streams stdout/stderr to a live **Logs** panel
  - Supports **Stop**, **Clear logs**, and optional **stdin** input

> Runs with working directory = the script’s folder (so relative imports and data paths work).



For the usages of .fseries in the Canon papers, see the source of the files https://david.fremlin.de/knots/index.htm.
% lines a_x(j) b_x(j) a_y(j) b_y(j) a_z(j) b_z(j) 
% corresponding to x(s) = sum a_x(j)cos(js)+b_x(j)sin(js) etc