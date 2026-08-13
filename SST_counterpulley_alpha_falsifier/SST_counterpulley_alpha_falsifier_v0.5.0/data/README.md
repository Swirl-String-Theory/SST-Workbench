# Geometry data

`ideal_3_1_1.txt` contains only the `Id="3:1:1"` AB Fourier block extracted from the user's larger `ideal.txt` table.

The parser also accepts the full original `ideal.txt` file:

```bat
python run_all_checks.py --data C:\path\to\ideal.txt --out-dir audit_original_table
```

No fitted alpha information is stored in this geometry block.
