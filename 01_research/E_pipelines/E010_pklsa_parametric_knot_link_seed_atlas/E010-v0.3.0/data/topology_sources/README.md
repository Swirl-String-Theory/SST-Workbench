# Bundled topology databases

`linkinfo_data_complete.xls` is the user-supplied LinkInfo legacy Excel database for this builder session. `knotinfo_data_complete.xls.zip` is the KnotInfo legacy database archive carried forward from the PKLSA v0.2.0 source integration.

The builder never edits these files. It computes exact source SHA-256 values and reads them with `xlrd` into a derived registry that records workbook, sheet, row and raw fields.

The ingestion policy is fail-closed: unknown schemas, missing labels or unavailable `xlrd` abort database ingestion instead of inventing a Rolfsen/Thistlethwaite mapping.
