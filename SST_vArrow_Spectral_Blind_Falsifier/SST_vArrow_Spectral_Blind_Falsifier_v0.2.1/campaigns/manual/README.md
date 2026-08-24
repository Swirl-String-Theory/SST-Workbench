# Manual campaign overrides

Place a `manifest.csv` here (or in any nested campaign directory) to explicitly define samples. Example:

```csv
sample_id,family_id,topology,resolution_n,input_type,path,core_radius_m
trefoil_300,trefoil,BLIND_A,300,trajectory_npz,data\trefoil_300.npz,1.40897017e-15
trefoil_600,trefoil,BLIND_A,600,trajectory_npz,data\trefoil_600.npz,1.40897017e-15
```

Paths are resolved relative to the manifest that contains them. Explicit manifest rows take precedence over recursively discovered raw files.
