# Importa los módulos necesarios
import os
import re
import argparse
import subprocess
import threading
import time
import psutil
import math
from rich import print
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Console
from rich.progress import Progress
from rich.live import Live
from rich.table import Table
from rich.text import Text

# Función para ejecutar el comando wget
def run_wget(command, download_directory):
    subprocess.run(command, shell=True, cwd=download_directory)

# Función para descargar un sitio web de forma recursiva

def download_website(url, download_directory, verbose=False):
    """Descarga el sitio web de forma recursiva en el directorio especificado."""
    os.makedirs(download_directory, exist_ok=True)
    command = f"wget --recursive --page-requisites --convert-links --restrict-file-names=windows --no-parent {url}"
    if not verbose:
        command += " --quiet"
    command += " 2>/dev/null"

    wget_thread = threading.Thread(target=run_wget, args=(command, download_directory))
    wget_thread.start()

    console = Console()
    start_time = time.time()

    previous_write_bytes = 0
    previous_time = time.time()

    while wget_thread.is_alive():
        time.sleep(1)
        elapsed_time = time.time() - start_time
        elapsed_minutes, elapsed_seconds = divmod(int(elapsed_time), 60)

        # Obtén información del proceso wget
        for proc in psutil.process_iter(["name", "cmdline", "io_counters"]):
            if proc.info["name"] == "wget" and proc.info["cmdline"]:
                io_counters = proc.info["io_counters"]
                read_bytes = io_counters.read_bytes
                write_bytes = io_counters.write_bytes

                # Calcular la velocidad de descarga en KB/s
                current_time = time.time()
                if current_time - previous_time >= 1:
                    time_interval = current_time - previous_time
                    download_speed = (write_bytes - previous_write_bytes) / (1024 * time_interval)
                    previous_write_bytes = write_bytes
                    previous_time = current_time

        # Contar el número de archivos descargados
        num_files_downloaded = sum(len(files) for _, _, files in os.walk(download_directory))

        console.print(f"Archivos descargados: {num_files_downloaded} | Velocidad de descarga: {download_speed:.2f} KB/s | Tiempo transcurrido: {elapsed_minutes:02d}:{elapsed_seconds:02d}", end="\r")

    console.print()
    wget_thread.join()

# Función para buscar plugins de WordPress en el directorio especificado
def find_plugins(directory):
    """Busca plugins de WordPress y sus versiones en el directorio especificado."""
    # Expresiones regulares para detectar plugins y versiones
    plugin_pattern = re.compile(r'/wp-content/plugins/([^/]+)')
    version_pattern = re.compile(r'Version:\s*([\d.]+)')
    url_version_pattern = re.compile(r'[&@]?ver=([\d.]+)')

    # Diccionario para almacenar información sobre plugins encontrados
    found_plugins = {}

    # Recorre el directorio de forma recursiva
    for root, _, files in os.walk(directory):
        for file in files:
            # Busca en archivos .html, .css, .js y .php
            if file.endswith(('.html', '.css', '.js', '.php')):
                file_path = os.path.join(root, file)

                # Abre el archivo y lee sus líneas
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                    # Busca plugins en cada línea del archivo
                    for i, line in enumerate(lines):
                        matches = plugin_pattern.findall(line)
                        if matches:
                            for match in matches:
                                # Almacena información sobre el plugin encontrado si no está en el diccionario
                                if match not in found_plugins:
                                    context = ''.join(lines[max(0, i-5):i+6])
                                    version = None
                                    # Busca la versión del plugin
                                    if file.endswith('.php'):
                                        for l in lines:
                                            version_match = version_pattern.search(l)
                                            if version_match:
                                                version = version_match.group(1)
                                                break
                                    else:
                                        version_match = url_version_pattern.search(line)
                                        if version_match:
                                            version = version_match.group(1)

                                    found_plugins[match] = {
                                        'simple_path': os.path.relpath(file_path, directory),
                                        'full_path': file_path,
                                        'context': context,
                                        'version': version
                                    }


    # Muestra información sobre los plugins encontrados
    if found_plugins:  # Si se encontraron plugins
        print("[bold]Plugins encontrados:[/bold]")
        
        # Crear y abrir el archivo de texto para guardar la información de los plugins
        with open("plugins_info.txt", "w") as file:
            for plugin, plugin_info in found_plugins.items():
                version_str = f' (Versión {plugin_info["version"]})' if plugin_info["version"] else ' [red](Versión no encontrada)[/red]'
                if plugin_info["version"]:
                    version_str = f'[blink]{version_str}[/blink]'

                print(f'- [bold]{plugin}[/bold]{version_str} (en {plugin_info["simple_path"]})')
                print(f'  Ruta completa: {plugin_info["full_path"]}')
                print("  Contexto:")
                syntax = Syntax(plugin_info['context'], "html", line_numbers=True, start_line=max(1, i-5), highlight_lines={i})
                print(Panel(syntax))
                print()

                # Guardar la información del plugin y su versión en el archivo de texto
                if plugin_info["version"]:
                    file.write(f"{plugin}:{plugin_info['version']}\n")
                else:
                    file.write(f"{plugin}:unknown_version\n")

    else:  # Si no se encontraron plugins
        print("[blink][bold red]Ningún plugin encontrado[/bold][/blink]")

# Solicita la URL del sitio web, descarga el sitio y busca plugins

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Descarga y busca plugins de WordPress en un sitio web.")
    parser.add_argument("url", help="URL del sitio web donde se buscarán los plugins de WordPress.")
    parser.add_argument("-v", "--verbose", help="Muestra la salida detallada de wget durante la descarga del sitio web.", action="store_true")
    args = parser.parse_args()

    download_directory = "directorio_descargado"
    download_website(args.url, download_directory, args.verbose)

    console = Console()
    with console.status("[bold green]Analizando archivos descargados...\n") as status:
        find_plugins(download_directory)
