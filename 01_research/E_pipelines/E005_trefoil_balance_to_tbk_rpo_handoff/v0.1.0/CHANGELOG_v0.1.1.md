# v0.1.1 — runtime routing hotfix

No scientific selection rule, q/h/p value, geometry, target gate, target config,
or promotion rule is changed.

Fixes:

1. Detect v0.4.8 external SYCL/DD32 worker availability before the spectral run.
2. If DD32 is unavailable, automatically use CPU/OpenMP for the same locked
   adaptive spectral ladder.
3. If DD32 fails after a positive probe, delete only the incomplete spectral
   stage and retry it with CPU/OpenMP.
4. Fix `run_all.cmd` exit-code loss caused by `%ERRORLEVEL%` expansion inside
   a parenthesized IF block.
5. Remove literal `>` characters from batch banners; they were interpreted by
   CMD as redirection and caused `The system cannot find the path specified.`
6. Add `run_resume_after_screen_v048.cmd` and an exact hash check so a completed
   FP64 screen can be reused without rerunning it.

Observed target failure handled by this release:

```text
SYCL requested but external worker is unavailable:
{'available': False, 'returncode': 3221225781, 'stderr': ''}
```

`3221225781 == 0xC0000135`, Windows `STATUS_DLL_NOT_FOUND`.
