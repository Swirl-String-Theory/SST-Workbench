# Ship outputs and zips under 50MB

Unpacked `outputs/` stay gitignored (25k files / ~5GB would blow GitHub and `git status`). Outputs still go to GitHub as sibling `*_outputs.zip`, or as `*.zip.partNN` when the archive is 50–500 MiB. Any other pack-adjacent `.zip` under 50 MiB is force-added. Restore_Archives stays local. Files at or above 50 MiB are never committed whole.
