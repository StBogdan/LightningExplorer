# Utility scripts
Found in `_scripts`, they do the heavy lifting.
- **utils_config.py**
  - Handles configuration
- **utils_databasePopulate.py**
  - Handles data from files to database
- **utils_db_upkeep.py**
  - More general script that `utils_databasePopulate`, also handles metric generation
  
Legacy (currently not easily usable):
- **utils_metrics.py**
  - Create data for graphs, dump it as JSON
- **utils_IP.py**
  - Keep list of addresses in the network
- **utils_networkView.py**
  - Keep good connections within the network
