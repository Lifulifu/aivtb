rem Starting the server in PowerShell
start powershell -NoExit -Command "cd server; python -m uvicorn --port 8000 server:app"
timeout /t 3 /nobreak

rem Starting the admin development server in PowerShell
start powershell -NoExit -Command "cd admin; yarn dev --port 5173;"

rem Starting the subtitle development server in PowerShell
start powershell -NoExit -Command "cd subtitle; yarn dev --port 5174;"

start http://localhost:5173
start http://localhost:5174