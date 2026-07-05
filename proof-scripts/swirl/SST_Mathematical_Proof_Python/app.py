# Streamlit app to explore and run SST modules
import json, sys, pathlib, importlib.util, runpy, inspect, re, os
import streamlit as st
import subprocess, time, threading
import streamlit.components.v1 as components
from typing import Any, Optional
import pandas as _pd

try:
    import plotly.graph_objects as go  # noqa: F401
    _HAS_PLOTLY = True
except Exception:
    _HAS_PLOTLY = False

APP_DIR = pathlib.Path(__file__).resolve().parent
SRC_DIR = APP_DIR / ""
INDEX_FILE = APP_DIR / "module_index.json"

# Ensure SST source directory is importable if needed
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

st.set_page_config(page_title="SST Explorer", layout="wide")

@st.cache_data(show_spinner=False)
def load_index():
    with INDEX_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"<<Error reading file: {e}>>"

def load_module_from_path(abs_path: pathlib.Path):
    """Load a Python module from an absolute path without relying on packages."""
    module_name = f"_sst_{abs_path.stem.replace('-', '_').replace(' ', '_')}_{abs(hash(abs_path)) & 0xFFFF}"
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader, "Could not create module loader"
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

def nice_name(rel_path: str) -> str:
    return rel_path.replace("\\\\", "/")

def _sanitize_rel_key(rel: str) -> str:
    """Sanitize a path string for use in Streamlit widget keys."""
    return rel.replace("/", "_").replace("\\", "_").replace(" ", "_")

# ---- Process & logging helpers ----
if "proc_map" not in st.session_state:
    st.session_state["proc_map"] = {}   # key -> subprocess.Popen
if "log_map" not in st.session_state:
    st.session_state["log_map"] = {}    # key -> list[str]
if "auto_scroll" not in st.session_state:
    st.session_state["auto_scroll"] = True
if "start_time_map" not in st.session_state:
    st.session_state["start_time_map"] = {}  # key -> epoch float for asset discovery
if "log_poll_until" not in st.session_state:
    st.session_state["log_poll_until"] = {}  # key -> epoch until which to keep polling for logs
if "plotly_active" not in st.session_state:
    st.session_state["plotly_active"] = None

def _script_key(rel: str) -> str:
    return rel.replace("\\\\","/")

def _is_running(key: str) -> bool:
    p = st.session_state["proc_map"].get(key)
    return bool(p) and (p.poll() is None)

# ---- Thread-safe log buffering (avoid session_state in threads) ----
_GLOBAL_LOGS: dict[str, list[str]] = {}
_GLOBAL_LOGS_LOCK = threading.Lock()

def _mark_poll_window(key: str, seconds: float = 2.0):
    st.session_state["log_poll_until"][key] = time.time() + seconds

def _needs_polling(key: str) -> bool:
    return time.time() < st.session_state["log_poll_until"].get(key, 0.0)

def _append_log(key: str, text: str):
    """Append a log line in a thread-safe module buffer (not session_state)."""
    with _GLOBAL_LOGS_LOCK:
        _GLOBAL_LOGS.setdefault(key, []).append(text)

def _drain_logs_to_session(key: str) -> bool:
    """Move any pending buffered logs for a key into session_state for UI rendering."""
    # Ensure session state container exists
    if "log_map" not in st.session_state:
        st.session_state["log_map"] = {}
    with _GLOBAL_LOGS_LOCK:
        pending = _GLOBAL_LOGS.pop(key, [])
    if pending:
        st.session_state["log_map"].setdefault(key, []).extend(pending)
        _mark_poll_window(key)
        return True
    return False

def _launch_script(abs_path: pathlib.Path, extra_args: Optional[list[str]] = None, pre_stdin: Optional[str] = None):
    key = _script_key(str(abs_path.relative_to(SRC_DIR)))
    # Ensure buffer
    st.session_state["log_map"][key] = []
    # Record start time for asset discovery
    st.session_state["start_time_map"][key] = time.time()
    _mark_poll_window(key, seconds=5.0)  # Extended polling window
    # Start subprocess with realtime stdout+stderr
    cmd = [sys.executable, "-u", str(abs_path)] + (extra_args or [])
    cmd_str = " ".join(cmd)
    _append_log(key, f">>> Starting: {cmd_str}")
    _append_log(key, ">>> Output will appear below...")
    _drain_logs_to_session(key)  # Immediately show startup message
    try:
        # Force unbuffered output via environment
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        p = subprocess.Popen(
            cmd,
            cwd=str(abs_path.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=0,  # Unbuffered
            encoding="utf-8",
            errors="replace",
            env=env,
        )
    except Exception as e:
        _append_log(key, f"<<launch error: {e}>>")
        _drain_logs_to_session(key)
        return key
    st.session_state["proc_map"][key] = p
    # Optionally prime stdin
    try:
        if pre_stdin and p.stdin and p.poll() is None:
            p.stdin.write(pre_stdin + ("" if pre_stdin.endswith("\n") else "\n"))
            p.stdin.flush()
            _append_log(key, f">>> Pre-sent stdin: {pre_stdin!r}")
            _drain_logs_to_session(key)
    except Exception as e:
        _append_log(key, f"<<stdin prime error: {e}>>")
        _drain_logs_to_session(key)

    def _reader():
        try:
            # Read all output - both line-by-line and remaining
            output_lines = []
            while True:
                line = p.stdout.readline()
                if not line:
                    # Check if process is still running
                    if p.poll() is not None:
                        break
                    # Process still running but no output yet, wait a bit
                    time.sleep(0.01)
                    continue
                output_lines.append(line.rstrip("\n"))
                _append_log(key, line.rstrip("\n"))
            
            # Read any remaining output after process ends
            try:
                rest = p.stdout.read()
                if rest:
                    for ln in rest.splitlines():
                        _append_log(key, ln)
            except Exception:
                pass
        except Exception as e:
            _append_log(key, f"<<reader error: {e}>>")
        finally:
            rc = p.poll()
            if rc is not None:
                _append_log(key, f"<<process exited with code {rc}>>")
            else:
                _append_log(key, "<<process ended>>")

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    return key

def _send_stdin(key: str, text: str):
    p = st.session_state["proc_map"].get(key)
    if p and p.poll() is None and p.stdin:
        try:
            p.stdin.write(text + "\n")
            p.stdin.flush()
        except Exception as e:
            _append_log(key, f"<<stdin error: {e}>>")

def _stop_script(key: str):
    p = st.session_state["proc_map"].get(key)
    if not p: 
        return
    try:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                p.kill()
    except Exception as e:
        _append_log(key, f"<<terminate error: {e}>>")

# ---- Discovery helpers ----
def discover_py_files_recursively(root: pathlib.Path) -> list[str]:
    """Return relative paths (to SRC_DIR) of all *.py under root, excluding app and typical junk."""
    skip_dirs = {".git", ".hg", ".svn", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache", ".pytest_cache"}
    rels = []
    for p in root.rglob("*.py"):
        if p.name == "app.py":
            continue
        parts = set(p.parts)
        if parts & skip_dirs:
            continue
        try:
            rels.append(str(p.relative_to(SRC_DIR)))
        except ValueError:
            # Not under SRC_DIR
            continue
    return sorted(set(rels))

def _list_assets_since(folder: pathlib.Path, since_epoch: float):
    """List image/HTML assets in folder modified at/after since_epoch."""
    patterns = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.html", "*.csv", "*.json"]
    assets = []
    for pat in patterns:
        for f in folder.glob(pat):
            try:
                mtime = f.stat().st_mtime
            except OSError:
                continue
            if mtime >= since_epoch:
                assets.append((f, mtime))
    assets.sort(key=lambda t: t[1], reverse=True)
    return [f for f, _ in assets]

def _maybe_auto_rerun(name: str, interval_sec: float = 1.0):
    """
    Lightweight periodic rerun without external plugins.
    Triggers st.rerun()/experimental_rerun at most once per interval.
    """
    flag = f"__auto_rerun_{name}_last"
    now = time.time()
    last = st.session_state.get(flag, 0.0)
    if now - last >= interval_sec:
        st.session_state[flag] = now
        try:
            # Prefer modern API when available
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()
        except Exception:
            # Ignore if rerun not permitted in this context
            pass

def sidebar_summary(idx, show_sidebar=True, tab_key=""):
    """Show global sidebar summary. If show_sidebar=False, just return filtered index."""
    if show_sidebar:
        st.sidebar.header("SST Explorer")
        st.sidebar.write(f"Discovered **{len(idx)}** Python files")
        # Use unique key based on tab to avoid duplicate element IDs
        only_st = st.sidebar.checkbox("Only modules that import Streamlit", value=False, key=f"only_st_{tab_key}")
        return [m for m in idx if (not only_st or m.get("imports_streamlit"))]
    else:
        # Just return all if sidebar not shown
        return idx

# ---- Plotly detection and rendering ----
_PLOTLY_FN_CANDIDATES = (
    "st_app",
    "plotly_app",
    "plotly_view",
    "build_plotly",
    "get_plotly_figure",
    "get_fig",
    "plot",
    "render_plotly",
)

def _detect_plotly_entry(mod: Any) -> Optional[str]:
    for name in _PLOTLY_FN_CANDIDATES:
        if hasattr(mod, name) and callable(getattr(mod, name)):
            return name
    return None

def _file_mentions_plotly(abs_path: pathlib.Path) -> bool:
    try:
        txt = read_text(abs_path)
        return ("plotly" in txt.lower())
    except Exception:
        return False

def _file_uses_matplotlib(abs_path: pathlib.Path) -> bool:
    """Detect if a file uses matplotlib."""
    try:
        text = read_text(abs_path)
        return any(keyword in text.lower() for keyword in [
            "import matplotlib", "from matplotlib", "plt.", "matplotlib.pyplot",
            "mpl_toolkits", "fig.add_subplot", "projection='3d'"
        ])
    except Exception:
        return False

def _file_has_3d_plotting(abs_path: pathlib.Path) -> bool:
    """Detect if a file has 3D plotting (matplotlib or plotly)."""
    try:
        text = read_text(abs_path)
        return any(keyword in text for keyword in [
            "projection='3d'", "Axes3D", "plotly.graph_objects", "go.Scatter3d",
            "go.Cone", "go.Surface", "plotly.express", "px.scatter_3d"
        ])
    except Exception:
        return False

def render_plotly_inline(abs_path: pathlib.Path):
    if not _HAS_PLOTLY:
        st.error("plotly is not installed in this environment.")
        return
    try:
        mod = load_module_from_path(abs_path)
    except Exception as e:
        st.exception(e)
        return
    entry = _detect_plotly_entry(mod)
    try:
        if entry == "st_app":
            mod.st_app()
            return
        if entry:
            obj = getattr(mod, entry)()
        else:
            # Try common names in order
            for name in ("get_plotly_figure", "get_fig", "build_plotly", "plot"):
                if hasattr(mod, name):
                    obj = getattr(mod, name)()
                    break
            else:
                st.warning("No Plotly entry found. Expose st_app() or a function returning a plotly Figure.")
                return
        # Render results
        if isinstance(obj, list):
            for i, it in enumerate(obj):
                try:
                    st.plotly_chart(it, width='stretch')
                except Exception:
                    st.write(f"[item {i}] {type(it)}")
        else:
            st.plotly_chart(obj, width='stretch')
    except Exception as e:
        st.exception(e)

def home_tab(filtered_idx):
    st.title("SST Streamlit Explorer")
    st.write(
        "Browse and run modules from **SST_Mathematical_Proof_Python**. "
        "To make a file runnable as a page, add an entrypoint like `st_app()` or `main()`."
    )
    st.subheader("Discovered modules")
    for m in filtered_idx:
        with st.expander(nice_name(m["path"])):
            st.caption("Imports Streamlit: **{}** · Candidate: **{}**".format(
                "yes" if m.get("imports_streamlit") else "no", m.get("candidate") or "—"
            ))
            if m.get("module_doc"):
                st.write(m["module_doc"])
            cols = st.columns(2)
            with cols[0]:
                st.markdown("**Functions**")
                for f in m["functions"][:24]:
                    req = f.get("required_pos_args", 0)
                    st.write(f"- `{f['name']}` (requires {req} args)")
            with cols[1]:
                st.markdown("**Classes**")
                for c in m["classes"][:24]:
                    st.write(f"- `{c['name']}`")

def module_runner_tab(idx):
    st.header("Module Runner / Script Runner")
    items = [m["path"] for m in idx]
    choice = st.selectbox("Choose a module", items, index=0 if items else None)
    if not choice:
        return
    selected = next(m for m in idx if m["path"] == choice)
    st.write(f"**Selected:** `{choice}`")
    rel = selected["path"]
    abs_path = SRC_DIR / rel
    st.code(read_text(abs_path)[:2000] + ("\n... (truncated)" if abs_path.stat().st_size > 2000 else ""), language="python")

    candidate = selected.get("candidate")
    colA, colB, colC = st.columns(3)

    # --- Entrypoint runner (same-process import) ---
    with colA:
        st.subheader("Entrypoint (inline)")
        st.caption("Runs `st_app()`, `main()`, or `app()` inside this Streamlit process, if present.")
        
        # Initialize output capture for inline execution
        inline_key = f"inline_{_script_key(rel)}"
        if "inline_output" not in st.session_state:
            st.session_state["inline_output"] = {}
        if inline_key not in st.session_state["inline_output"]:
            st.session_state["inline_output"][inline_key] = []
        
        # Allow running even without a candidate - for scripts with top-level code
        run_button_disabled = False  # Allow running any script
        if st.button("Run module entrypoint" + (f" `{candidate}`" if candidate else " (or top-level code)"), disabled=run_button_disabled):
            # Clear previous output
            st.session_state["inline_output"][inline_key] = []
            try:
                import io
                import contextlib
                
                # Capture stdout and stderr
                output_buffer = io.StringIO()
                with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                    # Load module - this executes top-level code
                    mod = load_module_from_path(abs_path)
                    
                    # Try to call entrypoint if it exists
                    func = None
                    if candidate and hasattr(mod, candidate):
                        func = getattr(mod, candidate)
                    elif hasattr(mod, "st_app"):
                        func = getattr(mod, "st_app")
                    elif hasattr(mod, "main"):
                        func = getattr(mod, "main")
                    elif hasattr(mod, "app"):
                        func = getattr(mod, "app")
                    
                    if callable(func):
                        func()
                
                # Get captured output
                captured = output_buffer.getvalue()
                if captured:
                    st.session_state["inline_output"][inline_key] = captured.splitlines()
                else:
                    st.session_state["inline_output"][inline_key] = ["(No output captured - module loaded but produced no stdout/stderr)"]
                    
            except Exception as e:
                st.session_state["inline_output"][inline_key] = [f"Error: {str(e)}", f"Traceback: {repr(e)}"]
                st.exception(e)
        
        # Show captured output
        inline_logs = "\n".join(st.session_state["inline_output"].get(inline_key, []))
        if inline_logs:
            st.code(inline_logs, language="text")
        else:
            st.info("Click 'Run module entrypoint' to see output here.")
        
        if not candidate and not any(hasattr(load_module_from_path(abs_path), name) for name in ("st_app","main","app")):
            st.info("No inline entrypoint found. For scripts that just print, use 'Run as Script (subprocess)' on the right.")

    # --- Script runner (subprocess) with live logs ---
    with colB:
        st.subheader("Run as Script (subprocess)")
        st.caption("Launches `python -u <file>.py` and streams stdout/stderr below. Works even without a `main()`.")
        key = _script_key(rel)
        argrow = st.columns(3)
        args_str = argrow[0].text_input("Args", key="args_"+key, placeholder="e.g. exact_closure")
        prein_str = argrow[1].text_input("Pre-send stdin", key="prein_"+key, placeholder="e.g. y")
        argrow[2].caption("Optional arguments and first input lines")
        cols = st.columns(4)
        if cols[0].button("▶️ Start script", key="start_"+key):
            extra = [s for s in (args_str or "").split() if s] or None
            _launch_script(abs_path, extra_args=extra, pre_stdin=(prein_str or None))
            # Don't rerun immediately - let auto-refresh handle it
        if cols[1].button("⏹ Stop", key="stop_"+key, disabled=not _is_running(key)):
            _stop_script(key)
        clear_req = cols[2].button("🧹 Clear logs", key="clear_"+key)
        if clear_req:
            st.session_state["log_map"][key] = []
        # Test button to verify output capture works
        if cols[3].button("🧪 Test", key="test_"+key):
            test_script = pathlib.Path(__file__).parent / "_test_output.py"
            # Write test script with explicit unbuffered Python
            test_script.write_text('import sys\nimport time\n# Force unbuffered output\nif hasattr(sys.stdout, "reconfigure"):\n    sys.stdout.reconfigure(line_buffering=True)\nfor i in range(5):\n    print(f"Test line {i+1}", flush=True)\n    time.sleep(0.2)\nprint("Test complete!", flush=True)\n')
            # Manually set up the same key so output appears in the same log box
            st.session_state["log_map"][key] = []
            st.session_state["start_time_map"][key] = time.time()
            _mark_poll_window(key, seconds=5.0)
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            p = subprocess.Popen(
                [sys.executable, "-u", str(test_script)],
                cwd=str(test_script.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=0,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
            st.session_state["proc_map"][key] = p
            _append_log(key, f">>> Test script started")
            _drain_logs_to_session(key)
            def _test_reader():
                try:
                    while True:
                        line = p.stdout.readline()
                        if not line:
                            if p.poll() is not None:
                                break
                            time.sleep(0.01)
                            continue
                        _append_log(key, line.rstrip("\n"))
                    # Read remaining
                    try:
                        rest = p.stdout.read()
                        if rest:
                            for ln in rest.splitlines():
                                _append_log(key, ln)
                    except Exception:
                        pass
                except Exception as e:
                    _append_log(key, f"<<reader error: {e}>>")
                finally:
                    rc = p.poll()
                    if rc is not None:
                        _append_log(key, f"<<test exited with code {rc}>>")
            threading.Thread(target=_test_reader, daemon=True).start()

        with st.expander("Send stdin (optional)"):
            send_txt = st.text_input("Line to send", key="stdin_"+key)
            if st.button("Send", key="send_"+key, disabled=not _is_running(key)):
                _send_stdin(key, send_txt or "")

        proc = st.session_state["proc_map"].get(key)
        running = _is_running(key)
        status = "running" if running else (f"exit {proc.returncode}" if proc and proc.poll() is not None else "idle")
        
        # Drain any background logs to session_state before rendering
        had_new = _drain_logs_to_session(key)
        logs = "\n".join(st.session_state["log_map"].get(key, []))
        log_count = len(st.session_state["log_map"].get(key, []))
        
        st.caption(f"Status: {status} | Log lines: {log_count} | Polling: {_needs_polling(key)}")
        
        # Use a container that can be updated
        log_container = st.empty()
        if logs:
            log_container.code(logs, language="text")
        else:
            log_container.info("No output yet. Click 'Start script' to run. Output will appear here.")
        
        # Auto-refresh if running or recently finished or if we just got new logs
        if running or _needs_polling(key) or had_new:
            _maybe_auto_rerun("module_"+key, interval_sec=0.5)  # Faster refresh

        # Asset preview for scripts (images/HTML created since start)
        st.markdown("**New assets (since start):**")
        since = st.session_state["start_time_map"].get(key, 0.0)
        assets = _list_assets_since(abs_path.parent, since) if since else []
        if not assets:
            st.caption("No new assets detected yet.")
        else:
            for asset in assets[:12]:
                if asset.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
                    st.image(str(asset), caption=asset.name, width='stretch')
                elif asset.suffix.lower() == ".svg":
                    try:
                        svg_text = asset.read_text(encoding="utf-8", errors="ignore")
                        components.html(svg_text, height=300, scrolling=True)
                    except Exception:
                        st.write(f"[SVG] {asset.name}")
                elif asset.suffix.lower() == ".html":
                    try:
                        html_text = asset.read_text(encoding="utf-8", errors="ignore")
                        components.html(html_text, height=360, scrolling=True)
                    except Exception:
                        st.write(f"[HTML] {asset.name}")
                elif asset.suffix.lower() == ".csv":
                    try:
                        df_prev = _pd.read_csv(asset)
                        st.dataframe(df_prev.head(50))
                        st.download_button("Download CSV", data=asset.read_bytes(), file_name=asset.name, mime="text/csv", key="dl_mod_"+asset.name)
                    except Exception:
                        st.write(f"[CSV] {asset.name}")
                elif asset.suffix.lower() == ".json":
                    try:
                        st.code((asset.read_text(encoding="utf-8", errors="ignore"))[:5000])
                        st.download_button("Download JSON", data=asset.read_bytes(), file_name=asset.name, mime="application/json", key="dlm_json_"+asset.name)
                    except Exception:
                        st.write(f"[JSON] {asset.name}")
            if len(assets) > 12:
                st.caption(f"... and {len(assets)-12} more")

    # --- Plotly inline renderer ---
    with colC:
        st.subheader("Plotly Renderer (inline)")
        if _file_mentions_plotly(abs_path):
            if st.button("Render Plotly inline", key="plotly_"+rel.replace("/","_")):
                render_plotly_inline(abs_path)
        else:
            st.caption("No obvious Plotly usage detected in file.")

def function_explorer_tab(idx):
    st.header("Function Explorer")
    flat = []
    for m in idx:
        for f in m["functions"]:
            flat.append((m, f))
    if not flat:
        st.info("No functions found.")
        return
    labels = [f"{nice_name(m['path'])} :: {f['name']} (req={f.get('required_pos_args',0)})" for (m,f) in flat]
    i = st.selectbox("Pick a function", range(len(flat)), format_func=lambda k: labels[k])
    m, f = flat[i]
    rel = m["path"]
    abs_path = SRC_DIR / rel
    st.write(f"**Module:** `{rel}`")
    st.write(f"**Function:** `{f['name']}` · requires **{f.get('required_pos_args',0)}** positional args")
    if f.get("doc"):
        st.code(f["doc"])
    if f.get("required_pos_args",0) == 0 and st.button("Run this function"):
        try:
            mod = load_module_from_path(abs_path)
            fn = getattr(mod, f["name"], None)
            if callable(fn):
                out = fn()
                if out is not None:
                    st.write("Return value:")
                    st.write(out)
            else:
                st.warning("Function not found or not callable at runtime.")
        except Exception as e:
            st.exception(e)
    else:
        st.caption("Add default arguments to make it runnable here.")

def code_viewer_tab(idx):
    st.header("Code Viewer")
    files = [m["path"] for m in idx]
    rel = st.selectbox("Choose a file", files)
    if not rel: return
    abs_path = SRC_DIR / rel
    st.code(read_text(abs_path), language="python")

def script_gallery_tab(all_paths):
    st.header("Script Gallery (recursive)")
    st.caption("Run any discovered Python script. Logs stream live; images/HTML created in the script folder are displayed automatically.")
    
    # Statistics
    mpl_count = sum(1 for p in all_paths if _file_uses_matplotlib(SRC_DIR / p))
    plotly_count = sum(1 for p in all_paths if _file_mentions_plotly(SRC_DIR / p))
    has_3d_count = sum(1 for p in all_paths if _file_has_3d_plotting(SRC_DIR / p))
    st.caption(f"📊 {mpl_count} use Matplotlib | ⚡ {plotly_count} use Plotly | 🎯 {has_3d_count} have 3D plotting")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        q = st.text_input("Filter by path substring", "")
    with col2:
        filter_type = st.selectbox("Filter by library", ["All", "Matplotlib only", "Plotly only", "3D plotting", "Matplotlib 3D (needs conversion)"])
    
    paths = [p for p in all_paths if (q.lower() in p.lower())] if q else all_paths
    
    # Apply library filter
    if filter_type == "Matplotlib only":
        paths = [p for p in paths if _file_uses_matplotlib(SRC_DIR / p)]
    elif filter_type == "Plotly only":
        paths = [p for p in paths if _file_mentions_plotly(SRC_DIR / p)]
    elif filter_type == "3D plotting":
        paths = [p for p in paths if _file_has_3d_plotting(SRC_DIR / p)]
    elif filter_type == "Matplotlib 3D (needs conversion)":
        paths = [p for p in paths if _file_uses_matplotlib(SRC_DIR / p) and _file_has_3d_plotting(SRC_DIR / p) and not _file_mentions_plotly(SRC_DIR / p)]
    if not paths:
        st.info("No scripts match the current filter.")
        return
    for idx, rel in enumerate(paths):
        abs_path = SRC_DIR / rel
        key = _script_key(rel)
        sanitized_rel = _sanitize_rel_key(rel)
        safe_key = f"{idx}_{sanitized_rel}"
        
        # Detect plotting libraries
        uses_mpl = _file_uses_matplotlib(abs_path)
        uses_plotly = _file_mentions_plotly(abs_path)
        has_3d = _file_has_3d_plotting(abs_path)
        
        # Create expander title with badges
        title = nice_name(rel)
        badges = []
        if uses_mpl:
            badges.append("📊 Matplotlib")
        if uses_plotly:
            badges.append("⚡ Plotly")
        if has_3d:
            badges.append("🎯 3D")
        if badges:
            title += " " + " ".join(badges)
        
        with st.expander(title, expanded=False):
            # Show library info
            if uses_mpl and has_3d and not uses_plotly:
                st.info("💡 This script uses Matplotlib 3D. Consider converting to Plotly 3D for better interactivity in Streamlit.")
            
            cols = st.columns(5)
            if cols[0].button("▶️ Start", key="gal_start_"+safe_key):
                _launch_script(abs_path)
            if cols[1].button("⏹ Stop", key="gal_stop_"+safe_key, disabled=not _is_running(key)):
                _stop_script(key)
            if cols[2].button("🧹 Clear logs", key="gal_clear_"+safe_key):
                st.session_state["log_map"][key] = []
            # Status display
            proc = st.session_state["proc_map"].get(key)
            status = "running" if _is_running(key) else (f"exit {proc.returncode}" if proc else "idle")
            cols[3].markdown(f"**Status:** {status}")
            # Plotly conversion button for matplotlib 3D scripts
            if uses_mpl and has_3d and not uses_plotly:
                if cols[4].button("🎯 Try Plotly 3D", key="gal_plotly_"+safe_key):
                    st.info("⚠️ Automatic conversion is experimental. For best results, manually convert like `rodin_plotly_app.py` or `sawshape_plotly_app.py`.")
                    st.caption("To convert manually:")
                    st.code(f"""
# Example conversion pattern:
# 1. Replace: import matplotlib.pyplot as plt
#    With: import plotly.graph_objects as go
# 2. Replace: fig = plt.figure(); ax = fig.add_subplot(111, projection='3d')
#    With: fig = go.Figure()
# 3. Replace: ax.plot3D(x, y, z) 
#    With: fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines'))
# 4. Replace: ax.quiver(x, y, z, u, v, w)
#    With: fig.add_trace(go.Cone(x=x, y=y, z=z, u=u, v=v, w=w))
# 5. Replace: plt.show()
#    With: st.plotly_chart(fig, width='stretch')
                    """, language="python")
            if _is_running(key) or _needs_polling(key):
                _maybe_auto_rerun("gal_"+key, interval_sec=1.0)
            with st.expander("Args / Pre-input"):
                args_g = st.text_input("Args", value="", key="gal_args_"+safe_key, placeholder="e.g. exact_closure")
                prein_g = st.text_area("Pre-send stdin", value="", key="gal_prein_"+safe_key, placeholder="lines to send on start")
                if st.button("Start with args", key="gal_start_args_"+safe_key):
                    extra = [s for s in (args_g or "").split() if s] or None
                    _launch_script(abs_path, extra_args=extra, pre_stdin=(prein_g or None))
            # Drain any background logs to session_state before rendering
            _drain_logs_to_session(key)
            logs = "\n".join(st.session_state["log_map"].get(key, []))
            st.text_area("Logs", value=logs, height=180, key="gal_logs_"+safe_key)
            with st.expander("Send stdin (optional)"):
                send_txt_g = st.text_input("Line to send", key="stdin_gal_"+safe_key)
                if st.button("Send (gallery)", key="send_gal_"+safe_key, disabled=not _is_running(key)):
                    try:
                        p = st.session_state["proc_map"].get(key)
                        if p and p.poll() is None and p.stdin:
                            p.stdin.write((send_txt_g or "") + "\n")
                            p.stdin.flush()
                    except Exception as e:
                        _append_log(key, f"<<stdin error: {e}>>")
            st.markdown("**New assets (since start):**")
            since = st.session_state["start_time_map"].get(key, 0.0)
            assets = _list_assets_since(abs_path.parent, since) if since else []
            if not assets:
                st.caption("No new assets detected yet.")
            else:
                for asset in assets[:12]:
                    if asset.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
                        st.image(str(asset), caption=asset.name, width='stretch')
                    elif asset.suffix.lower() == ".svg":
                        try:
                            svg_text = asset.read_text(encoding="utf-8", errors="ignore")
                            components.html(svg_text, height=300, scrolling=True)
                        except Exception:
                            st.write(f"[SVG] {asset.name}")
                    elif asset.suffix.lower() == ".html":
                        try:
                            html_text = asset.read_text(encoding="utf-8", errors="ignore")
                            components.html(html_text, height=360, scrolling=True)
                        except Exception:
                            st.write(f"[HTML] {asset.name}")
                    elif asset.suffix.lower() == ".csv":
                        try:
                            df_prev = _pd.read_csv(asset)
                            st.dataframe(df_prev.head(50))
                            st.download_button("Download CSV", data=asset.read_bytes(), file_name=asset.name, mime="text/csv", key="dlg_csv_"+safe_key+"_"+asset.name)
                        except Exception:
                            st.write(f"[CSV] {asset.name}")
                    elif asset.suffix.lower() == ".json":
                        try:
                            st.code((asset.read_text(encoding="utf-8", errors="ignore"))[:5000])
                            st.download_button("Download JSON", data=asset.read_bytes(), file_name=asset.name, mime="application/json", key="dlg_json_"+safe_key+"_"+asset.name)
                        except Exception:
                            st.write(f"[JSON] {asset.name}")
                if len(assets) > 12:
                    st.caption(f"... and {len(assets)-12} more")

def search_tab(idx):
    st.header("Search")
    q = st.text_input("Keyword or regex")
    if not q:
        st.info("Enter a search query.")
        return
    results = []
    for m in idx:
        rel = m["path"]
        text = read_text(SRC_DIR / rel)
        try:
            for match in re.finditer(q, text, flags=re.IGNORECASE):
                start = max(0, match.start()-80)
                end = min(len(text), match.end()+80)
                snippet = text[start:end].replace("\\n","↩")
                results.append((rel, snippet))
                if len(results) >= 200:
                    break
        except re.error as e:
            st.error(f"Invalid regex: {e}")
            return
    st.write(f"Found **{len(results)}** matches")
    for rel, snip in results:
        with st.expander(rel):
            st.write(snip)

tabs = st.tabs(["🏠 Home","▶️ Module/Script Runner","🖼 Script Gallery","⚡ Plotly Gallery","🧲 Rodin 3D","🌀 Saw Coil 3D","🎯 Saw Bowl 3D","🔗 Fat Knots 3D","⭐ Neutron Star","🔎 Function Explorer","📄 Code Viewer","🔍 Search"])

idx = load_index()
# Only show global sidebar on non-Plotly tabs (tabs 0, 1, 2, 3, 9, 10, 11)
# Plotly tabs (4-8) will have their own sidebars
plotly_tab_indices = {4, 5, 6, 7, 8}  # Rodin, Saw Coil, Saw Bowl, Fat Knots, Neutron Star
# We'll show sidebar conditionally in each tab
filtered_idx = idx  # Will be filtered in each tab that needs it

with tabs[0]:
    # Show global sidebar for Home tab
    filtered_idx = sidebar_summary(idx, tab_key="home")
    home_tab(filtered_idx)
with tabs[1]:
    # Show global sidebar for Module Runner tab
    filtered_idx = sidebar_summary(idx, tab_key="runner")
    module_runner_tab(filtered_idx)
indexed_paths = [m["path"] for m in idx]
discovered_paths = discover_py_files_recursively(SRC_DIR)
all_paths = sorted(set(indexed_paths) | set(discovered_paths))
with tabs[2]:
    # Show global sidebar for Script Gallery tab
    filtered_idx = sidebar_summary(idx, tab_key="gallery")
    script_gallery_tab(all_paths)

def plotly_gallery_tab(paths):
    st.header("Plotly Renderer (inline)")
    st.caption("Render modules that expose st_app() or a function returning a plotly Figure.")
    q = st.text_input("Filter by path substring (Plotly Gallery)", "")
    candidates = []
    for rel in paths:
        abs_path = SRC_DIR / rel
        if _file_mentions_plotly(abs_path):
            candidates.append(rel)
    if q:
        candidates = [p for p in candidates if q.lower() in p.lower()]
    if not candidates:
        st.info("No Plotly-capable modules found (by heuristic).")
        return
    for rel in candidates:
        abs_path = SRC_DIR / rel
        with st.expander(nice_name(rel), expanded=False):
            st.code(read_text(abs_path)[:1200] + ("...\n" if abs_path.stat().st_size > 1200 else ""), language="python")
            mounted = st.session_state.get("plotly_active") == rel
            cols = st.columns(2)
            if not mounted:
                if cols[0].button("Render", key="plt_render_"+rel.replace("/","_")):
                    st.session_state["plotly_active"] = rel
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
            else:
                if cols[0].button("Close view", key="plt_close_"+rel.replace("/","_")):
                    st.session_state["plotly_active"] = None
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
            if mounted:
                st.info("Active Plotly view. Use the sidebar controls defined by this module; adjustments persist.")
                render_plotly_inline(abs_path)

with tabs[3]:
    # Show global sidebar for Plotly Gallery tab
    filtered_idx = sidebar_summary(idx, tab_key="plotly_gallery")
    plotly_gallery_tab(all_paths)
with tabs[4]:
    # Plotly apps have their own sidebars - don't show global sidebar
    st.header("Rodin + Dipole Rings (embedded)")
    try:
        rodin_mod = load_module_from_path(SRC_DIR / "rodin_plotly_app.py")
        if hasattr(rodin_mod, "st_app") and callable(getattr(rodin_mod, "st_app")):
            rodin_mod.st_app()
        else:
            st.error("rodin_plotly_app.py does not expose st_app().")
    except Exception as e:
        st.exception(e)
with tabs[5]:
    # Plotly apps have their own sidebars - don't show global sidebar
    st.header("Saw-Shape Coil (embedded)")
    try:
        saw_mod = load_module_from_path(SRC_DIR / "sawshape_plotly_app.py")
        if hasattr(saw_mod, "st_app") and callable(getattr(saw_mod, "st_app")):
            saw_mod.st_app()
        else:
            st.error("sawshape_plotly_app.py does not expose st_app().")
    except Exception as e:
        st.exception(e)
with tabs[6]:
    # Plotly apps have their own sidebars - don't show global sidebar
    st.header("Saw Bowl 3D (embedded)")
    try:
        sawbowl_mod = load_module_from_path(SRC_DIR / "sawbowl_plotly_app.py")
        if hasattr(sawbowl_mod, "st_app") and callable(getattr(sawbowl_mod, "st_app")):
            sawbowl_mod.st_app()
        else:
            st.error("sawbowl_plotly_app.py does not expose st_app().")
    except Exception as e:
        st.exception(e)
with tabs[7]:
    # Plotly apps have their own sidebars - don't show global sidebar
    st.header("Fat Knots 3D (embedded)")
    try:
        fatknots_mod = load_module_from_path(SRC_DIR / "fat_knots_plotly_app.py")
        if hasattr(fatknots_mod, "st_app") and callable(getattr(fatknots_mod, "st_app")):
            fatknots_mod.st_app()
        else:
            st.error("fat_knots_plotly_app.py does not expose st_app().")
    except Exception as e:
        st.exception(e)
with tabs[8]:
    # Plotly apps have their own sidebars - don't show global sidebar
    st.header("Neutron Star Time Dilation (embedded)")
    try:
        ns_mod = load_module_from_path(SRC_DIR / "NeutronStarTimeDilation_plotly.py")
        if hasattr(ns_mod, "st_app") and callable(getattr(ns_mod, "st_app")):
            ns_mod.st_app()
        else:
            st.error("NeutronStarTimeDilation_plotly.py does not expose st_app().")
    except Exception as e:
        st.exception(e)
with tabs[9]:
    # Show global sidebar for Function Explorer tab
    filtered_idx = sidebar_summary(idx, tab_key="function_explorer")
    function_explorer_tab(filtered_idx)
with tabs[10]:
    # Show global sidebar for Code Viewer tab
    filtered_idx = sidebar_summary(idx, tab_key="code_viewer")
    code_viewer_tab(filtered_idx)
with tabs[11]:
    # Show global sidebar for Search tab
    filtered_idx = sidebar_summary(idx, tab_key="search")
    search_tab(filtered_idx)

def _sanitize_rel_key(rel: str) -> str:
    """Sanitize a path string for use in Streamlit keys."""
    return rel.replace('/', '_').replace('\\', '_').replace(' ', '_')