# Scraping-a-sistemas-web
## Proyecto: Scraping-a-sistemas-web

### Descripción
Este proyecto implementa un algoritmo de scraping que se ejecuta en un entorno virtual. Su objetivo principal es facilitar la extracción de datos de sitios web de manera eficiente y estructurada. Proporciona herramientas para parametrizar URLs, realizar crawling y scraping, y generar salidas en formatos JSON y CSV.

### Características
- **Crawling parametrizado**: Permite especificar la URL inicial y la profundidad del crawling.
- **Extracción de datos**: Genera archivos en formatos JSONL y CSV con los datos extraídos.
- **Configuración flexible**: Diseñado para ser escalable y adaptable a diferentes necesidades de scraping.
- **Entorno virtual**: Asegura un entorno controlado para la ejecución del algoritmo.

### Requisitos Previos
Antes de ejecutar este proyecto, asegúrate de tener instalados los siguientes componentes:
- **Python 3.8 o superior**: Lenguaje de programación utilizado.
- **Virtualenv**: Para crear un entorno virtual aislado.
- **Dependencias del proyecto**: Especificadas en el archivo `requirements.txt`.

### Instalación
Sigue estos pasos para instalar y configurar el proyecto:

1. Clona este repositorio:
    ```bash
    git clone [URL del repositorio]
    ```

2. Navega al directorio del proyecto:
    ```bash
    cd Scraping-a-sistemas-web
    ```

3. Crea y activa un entorno virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

4. Instala las dependencias necesarias:
    ```bash
    pip install -r requirements.txt
    ```

### Uso
#### 1. Realizar crawling
Ejecuta el siguiente comando para realizar el crawling de un sitio web:
```bash
python -m runners.cli crawl --start-url "https://www.peugeot.com.ar" --depth 2 --out data/peugeot_urls.json
```
- **`--start-url`**: URL inicial para el crawling.
- **`--depth`**: Profundidad máxima del crawling.
- **`--out`**: Archivo de salida con las URLs encontradas.

#### 2. Realizar scraping
Ejecuta el siguiente comando para extraer datos de las URLs obtenidas:
```bash
python -m runners.cli scrape --urls-file data/peugeot_urls.json --out-jsonl data/peugeot_pages.jsonl --out-csv data/peugeot_pages.csv
```
- **`--urls-file`**: Archivo con las URLs a scrapear.
- **`--out-jsonl`**: Archivo de salida en formato JSONL.
- **`--out-csv`**: Archivo de salida en formato CSV.

### Estructura del Proyecto
- **`runners/cli.py`**: Contiene los comandos principales para ejecutar el crawling y scraping.
- **`data/`**: Carpeta donde se almacenan los resultados generados.
- **`requirements.txt`**: Lista de dependencias necesarias para el proyecto.

### Contribuciones
Si deseas contribuir a este proyecto:
1. Haz un fork del repositorio.
2. Crea una rama para tu funcionalidad o corrección:
    ```bash
    git checkout -b feature/nueva-funcionalidad
    ```
3. Realiza tus cambios y haz un commit:
    ```bash
    git commit -m "Descripción de los cambios"
    ```
4. Envía un pull request.

### Licencia
Este proyecto está bajo la licencia Copyright (c) 2025 ezzz3. Consulta el archivo `LICENSE` para más detalles.

### Contacto
Si tienes preguntas o sugerencias, no dudes en contactarnos a través de [correo electrónico o enlace].
