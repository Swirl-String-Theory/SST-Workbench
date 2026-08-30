# Trefoil_Balance_Point_Campaign_v0.2.1

Fine K31 q/h/p sweep around the long-time zero from v0.2.0.

- 20 frozen q/h/p states
- only `load 3.1`
- standard run to **30,000**
- optional all-state continuation to **60,000**

## Standard

```bat
run_all.cmd
```

## Full long-horizon campaign

```bat
run_all_extended.cmd
```

This runs all 20 states to 30k and then continues all 20 to 60k.

If the 30k run already exists:

```bat
run_extended_only.cmd
run_40_analyze.cmd
run_90_pack_outputs.cmd
```

The analyzer automatically uses the 60k late window only if all 20 i60000 outputs exist.
