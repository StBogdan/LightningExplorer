# Lightning Explorer

### About

A website meant for visualizing information on the Lightning Network.

Built using Python 3, Django, LND, Postgres and a number of hastily written bash scripts that keep it all together.

### Documentation
- [Setting up](./_docs/Setup.md)
- [Utils scripts](./_docs/Utils.md)


### Quick start

- Download repo
- Get in virtualenv
- Install dependencies
- Make sure `_scripts/setup_check.py` is happy
- Make sure a database is reachable
- Run Django server
  - Locally via `python3 manage.py runserver`