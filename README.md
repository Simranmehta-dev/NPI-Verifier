# NPI Verifier

Checks whether physician respondents are real by validating their NPI number against
the public CMS NPPES registry, then shows the results in a Panel dashboard.
Built on public data only. The demo data is synthetic.

## What it does
1. Cleans the NPI and checks format and check digit offline (free, no network).
2. Looks up valid NPIs in the NPPES registry (with retries and backoff).
3. Compares the registry name with the name the respondent gave.
4. Labels each row: verified, name_mismatch, not_found, invalid_format, lookup_error.
5. Flags NPIs that appear more than once in the same file.

## Run it
```
pip install -r requirements.txt
python -m pytest -q
panel serve app.py --show
```
Choose "Demo (offline)" to run on synthetic data, or "Live NPPES registry" for real lookups.
Input CSV columns: `npi`, `first_name`, `last_name` (see data/sample_respondents.csv).

## Design
- `validation.py`: pure functions, no I/O.
- `client.py`: the only module that talks to the network. Retries on timeouts and 5xx.
- `verifier.py`: business logic. Depends on a `Registry` protocol, so tests and the demo
  swap in fakes without touching the logic.
- `frames.py`: pandas in and out. `app.py`: UI only, no business logic.

## Known limits
- Name matching is exact after lowercasing and stripping punctuation (no nicknames,
  no middle names, no maiden names).
- Live mode runs lookups in 5 threads. Check the registry's usage terms before
  running large files.
