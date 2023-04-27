# Importa los módulos necesarios
import subprocess
import time
from rich.prompt import Prompt
from rich import print
from rich.progress import Progress
from rich.text import Text
from rich.panel import Panel

# Imprimir mensaje de autor
author_text = Text("-Written by Gearcapitan with Chatgptv4-", style="bold")
author_text.stylize("blink", 0, len(author_text))
print(Panel.fit(author_text))

# Animación de carga
with Progress() as progress:
    task = progress.add_task("[cyan]Preparando...", total=100)
    for _ in range(100):
        time.sleep(0.02)
        progress.update(task, advance=1)

# Solicitar la URL al usuario
url = Prompt.ask("[bold green]Por favor, ingrese la URL del sitio web:[/bold green]")

# Ejecutar el primer script (WPStaticGPT.py) con la URL como argumento
subprocess.run(["python3", "WPStaticGPT.py", url], check=True)

# Ejecutar el segundo script (WpscanSearch.py)
subprocess.run(["python3", "WpscanSearch.py"], check=True)
