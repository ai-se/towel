import subprocess
import os
import webbrowser
from time import sleep
# Start Elasticsearch
subprocess.Popen(os.path.abspath("C:/elasticsearch-2.3.3/bin/elasticsearch.bat"), creationflags=subprocess.CREATE_NEW_CONSOLE)

# sleep(20)
# Start local server
subprocess.Popen(os.path.abspath("C:/Users/krishnr8/EDD/Sandbox/MLResearch/towel/src/site/site.bat"), creationflags=subprocess.CREATE_NEW_CONSOLE)
sleep(15)
# Open a browser page
url = "http://localhost:8080/hello"
webbrowser.open(url,new=2)