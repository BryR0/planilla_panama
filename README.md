# 🕸️ Scraper de Planilla Gobierno Central (Panamá)

Este script automatiza el proceso de extracción de datos públicos del portal de la Contraloría General de la República de Panamá. Extrae los registros de funcionarios por institución, incluyendo salarios, fechas de inicio y otros campos relevantes, y los exporta a un archivo Excel.

---

## 🚀 Características

- Recolección de datos de múltiples instituciones públicas.
- Uso de hilos para acelerar el scraping.
- Reintentos automáticos ante errores de red.
- Limpieza y conversión de datos (fechas, montos).
- Exportación a Excel (`.xlsx`).
- Registro del tiempo total de ejecución.

---

## 🧱 Requisitos

- Python 3.7+
- Paquetes:

```bash
pip install requests beautifulsoup4 pandas openpyxl
```

## 🧪 Uso

```bash
python gob_scrap.py
```
