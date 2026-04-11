import sys
sys.path.insert(0, 'src')
import fileinput

# Этот скрипт найдет в functions.py место, где используются запросы,
# и принудительно отключит предупреждения
file_path = 'src/functions.py'
with fileinput.FileInput(file_path, inplace=True) as file:
    for line in file:
        if 'import requests' in line:
            print(line + "import urllib3\nurllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)", end='')
        else:
            print(line, end='')

print("✅ Настройки SSL в коде обновлены!")
