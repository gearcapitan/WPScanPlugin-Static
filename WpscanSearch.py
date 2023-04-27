import sys
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

# Crear una instancia de consola para mostrar resultados
console = Console()

# Función para convertir una versión en un número decimal
def version_to_float(version):
    return float(".".join(version.split(".")[:2]))

# Función para extraer las vulnerabilidades de la página HTML
def extract_vulnerabilities(html):
    soup = BeautifulSoup(html, "html.parser")
    vulnerabilities = []

    # Buscar las filas de la tabla de vulnerabilidades
    for row in soup.select(".table_tableRow__cHvfD"):
        published_date = row.select_one(".versionLink_publishedDate__qh_KQ").text.strip()
        title = row.select_one(".versionLink_title__aeAFI").text.strip()
        fixed_version = row.select_one(".versionLink_itemInfo__j5_TG > span").text.strip().replace("Fixed in version ", "")

        vulnerabilities.append((published_date, title, fixed_version))

    return vulnerabilities

# Función para buscar vulnerabilidades de un plugin
def search_vulnerabilities(plugin_name, plugin_version, verbose):
    url = f"https://wpscan.com/plugin/{plugin_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }

    # Mostrar la URL si se activa el modo verbose
    if verbose:
        console.print(f"Buscando en: {url}")

    # Realizar la solicitud HTTP
    response = requests.get(url, headers=headers)
    html = response.text

    # Extraer las vulnerabilidades del HTML
    vulnerabilities = extract_vulnerabilities(html)

    # Crear una tabla para mostrar las vulnerabilidades
    table = Table(show_header=True, header_style="bold")
    table.add_column("Fecha")
    table.add_column("Vulnerabilidad")
    table.add_column("Versión corregida")
    table.add_column("Estado")

    # Agregar las vulnerabilidades a la tabla
    for published_date, title, fixed_version in vulnerabilities:
        if version_to_float(plugin_version) < version_to_float(fixed_version):
            status = "[blink][red]VULNERABLE[/blink][/red]"
        elif version_to_float(plugin_version) < version_to_float(fixed_version) + 0.1:
            status = "[blink][yellow]POSIBLE VULNERABLE[/blink][/yellow]"
        else:
            status = ""

        table.add_row(published_date, title, fixed_version, status)

    # Mostrar la tabla en la consola
    console.print(table)

# Función principal del programa
def main():
    verbose = "-v" in sys.argv

    # Leer el archivo de información de plugins
    with open("plugins_info.txt", "r") as file:
        for line in file:
            plugin_info = line.strip().split(":")

            # Verificar si la línea tiene información válida
            if len(plugin_info) < 2:
                console.print("[red]Error en la línea del archivo 'plugins_info.txt':[/red]", line.strip())
                continue

            plugin_name = plugin_info[0]
            plugin_version = plugin_info[1]

            console.print(f"Plugin: {plugin_name} {plugin_version}")

            # Buscar las vulnerabilidades del plugin
            search_vulnerabilities(plugin_name, plugin_version, verbose)

if __name__ == "__main__":
    main()

