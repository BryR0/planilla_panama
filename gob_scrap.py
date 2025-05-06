#!/usr/local/bin/python
# -*- coding: utf-8 -*-
import time
import requests
import pandas as pd
from os import cpu_count
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed


def request_retries(method, url, session=None, max_retries=5, initial_wait=2, **kwargs):
    attempt = 0
    wait_time = initial_wait
    session = session or requests.Session()

    while attempt < max_retries:
        try:
            attempt += 1
            if method.lower() == 'get':
                response = session.get(url, **kwargs)
            elif method.lower() == 'post':
                response = session.post(url, **kwargs)
            else:
                raise ValueError(
                    "Método HTTP no soportado: usa 'get' o 'post'."
                )

            if response.status_code == 200:
                return response
            else:
                print(
                    f"⚠️ Estado HTTP inesperado ({response.status_code}) en intento {attempt}", flush=True
                )
        except requests.exceptions.RequestException as e:
            print(f"🔁 Error en intento {attempt}: {e}", flush=True)

        time.sleep(wait_time)
        wait_time *= 2  # Exponencial

    print("❌ Se agotaron los intentos de conexión.", flush=True)
    return None


def parse_results_table(soup):
    table = soup.find('table', {'id': 'MainContent_gvResultado'})
    if not table:
        return []
    headers = [th.text.strip() for th in table.find_all('th')]
    rows = []
    for tr in table.find('tbody').find_all('tr'):
        cells = [td.text.strip() for td in tr.find_all('td')]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def get_hidden_inputs(soup):
    return {
        '__VIEWSTATE': soup.find('input', {'id': '__VIEWSTATE'})['value'],
        '__VIEWSTATEGENERATOR': soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value'],
        '__EVENTVALIDATION': soup.find('input', {'id': '__EVENTVALIDATION'})['value'],
    }


def scrape_institution(institucion, session, url, headers):
    try:
        print(f"🏛  Procesando: {institucion}", flush=True)
        refresh = request_retries('get', url, session=session, headers=headers)
        if not refresh:
            return []

        soup = BeautifulSoup(refresh.text, 'html.parser')
        inputs = get_hidden_inputs(soup)

        form_data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': inputs['__VIEWSTATE'],
            '__VIEWSTATEGENERATOR': inputs['__VIEWSTATEGENERATOR'],
            '__VIEWSTATEENCRYPTED': '',
            '__EVENTVALIDATION': inputs['__EVENTVALIDATION'],
            'ctl00$MainContent$ddlInstituciones': institucion,
            'ctl00$MainContent$txtNombre': '',
            'ctl00$MainContent$txtApellido': '',
            'ctl00$MainContent$txtCargo': '',
            'ctl00$MainContent$ddlEstado': '',
            'ctl00$MainContent$btnBuscar': 'Buscar'
        }

        post = request_retries('post', url, session=session,
                               data=form_data, headers=headers)
        if not post:
            return []

        soup = BeautifulSoup(post.text, 'html.parser')
        rows = parse_results_table(soup)

        for r in rows:
            r['INSTITUCION'] = institucion

        return rows

    except Exception as e:
        print(f"❌ Error en {institucion}: {e}", flush=True)
        return []


def get_instituciones(soup):
    dropdown = soup.find('select', {'id': 'MainContent_ddlInstituciones'})
    if not dropdown:
        print("❌ No se encontró el dropdown de instituciones.", flush=True)
        return []

    opciones = dropdown.find_all('option')
    instituciones = [
        opt['value'] for opt in opciones
        if opt['value'].strip() and opt['value'] != "-- Seleccione una institución --"
    ]
    return instituciones


def scrape_all():
    session = requests.Session()
    url = "https://www.contraloria.gob.pa/CGR.PLANILLAGOB.UI/Formas/Index"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": url
    }

    r = request_retries('get', url, session=session, headers=headers)
    if not r:
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    instituciones = get_instituciones(soup)
    print(f"🔍 Se encontraron {len(instituciones)} instituciones", flush=True)

    all_data = []

    with ThreadPoolExecutor(max_workers=cpu_count()-1) as executor:
        futures = [executor.submit(scrape_institution, inst, session, url, headers)
                   for inst in instituciones]

        for future in as_completed(futures):
            data = future.result()
            all_data.extend(data)

    return all_data


def main():
    start_time = time.time()
    data = scrape_all()
    df = pd.DataFrame(data)

    df['Salario'] = df['Salario'].replace(r'[\$,]', '', regex=True).astype(float)  # nopep8
    df['Gasto'] = df['Gasto'].replace(r'[\$,]', '', regex=True).astype(float)
    df['Fecha de Inicio'] = pd.to_datetime(df['Fecha de Inicio'], format='%d/%m/%Y',  errors='coerce')  # nopep8

    df.to_excel("planilla_gobierno_central.xlsx", index=False)
    print(f"\n✅ Exportados {len(df)} registros.", flush=True)

    elapsed = time.time() - start_time
    print(f"⏱️ Tiempo de ejecución: {elapsed:.2f} segundos.", flush=True)


if __name__ == "__main__":
    main()
