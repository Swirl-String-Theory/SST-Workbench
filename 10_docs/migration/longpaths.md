# SP03 — long path hygiene

| Setting | Value | Scope |
|---------|-------|-------|
| `git config core.longpaths` | `true` | local repo (`SST-Workbench`) and global user config |
| `HKLM\...\FileSystem\LongPathsEnabled` | `1` | Windows (already enabled on this machine) |

Longest tracked relative path at SP00 freeze: **231** characters. With a typical
root prefix this exceeds the legacy Windows `MAX_PATH` of 260 for some files.

`core.longpaths` covers git operations. `LongPathsEnabled` covers other Win32
tools that opt into long paths. Both must stay on through the stage-1 move peak
(deeper catalog path + still-long version directory names) before SP09 shortens
names.

Verification: `scripts/test_root_marker.py::test_long_path_create_and_checkout`.
