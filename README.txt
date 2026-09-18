Refresher steps when I come back to modify site after a long time

Steps to get setup on a new machine
1. Recreate a virtual environment from the requirements.txt file
2. Manually create env.py file in root directory. Not stored in repo to preserve secret info within. Will need to manually copy over or pull from live server for staging/PROD
3. Unpack demoData.zip
4. Use "python manage.py showmigrations" to check for db migrations. If any needed, use "python manage.py migrate"


Steps to locally test
1. Enable virtual environment with command ".venv\Scripts\activate"
2. Launch local server with command "python manage.py runserver"