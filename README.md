# Software_Engineering_Project_ModularMaterials

Roles:

Sprint 1-3:
Fatma: Requirements Engineer / Tester
Aylin: Requirements Engineer / Software Designer
Daniela: Projektmanager / developer
Ewan: developer / devops engineer


# Startup Linux:
systemctl --user start docker-desktop
docker compose up
docker compose run --rm module-generator

___RUN Script create_module.py:
python3 Scripts/create_module.py

___create_module should ask in the console:

    python3 Scripts/create_module.py
    === Create a New Learning Module ===
    Module title: 
    Author: 
    Version [1.0]: 
    Tags (comma-separated): 

    If Error: Title, author and version are required.


# Startup Windows in Powershell:
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker compose up

Run module generator (in a separate terminal)
docker compose run --rm module-generator

____RUN Script create_module.py:

python Scripts/create_module.py 
# or
py Scripts/create_module.py

____create_module should ask in the console:

    === Create a New Learning Module ===
    Module title: 
    Author: 
    Version [1.0]: 
    Tags (comma-separated): 

    If Error: Title, author and version are required.

