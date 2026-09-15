import sys, nbformat
from nbclient import NotebookClient
name = sys.argv[1]
nb = nbformat.read(name, as_version=4)
NotebookClient(nb, timeout=3600, kernel_name="python3", resources={"metadata": {"path": "."}}).execute()
nbformat.write(nb, name)
print("done", name)
