import re

with open('docker-compose.yml', 'r') as f:
    content = f.read()

old = '''    command: >
      bash -c "airflow db upgrade &&
               airflow users create --username admin --password admin
               --firstname Admin --lastname User --role Admin
               --email admin@trialscope.local"'''

new = '''    command: bash -c "airflow db upgrade && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@trialscope.local"'''

content = content.replace(old, new)

with open('docker-compose.yml', 'w') as f:
    f.write(content)

print("Fixed!")
