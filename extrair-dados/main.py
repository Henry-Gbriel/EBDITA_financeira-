#bibliotecas utilizadas 
import requests
import json
import pandas as pd
import psycopg2
import uuid
from datetime import datetime
from config import POSTGRES_CONFIG
from psycopg2.extras import execute_batch

def get_connection():
    return psycopg2.connect(
        host=POSTGRES_CONFIG['host'],
        port=POSTGRES_CONFIG['port'],
        user=POSTGRES_CONFIG['user'],
        password=POSTGRES_CONFIG['password'],
        dbname=POSTGRES_CONFIG['database'],
        sslmode="require"
    )


def download(url, payload, projeto_nome, ano, registro):

    headers = {'Content-Type': 'application/json'}

    try: 
        response = requests.post(url, headers=headers, data=json.dumps(payload))
    except Exception as e:
        print(f"Erro na requisição do ano {ano} ({projeto_nome}): {e}")
        return

    if response.status_code != 200:
        print(f"Erro na requisição do ano {ano} ({projeto_nome}):", response.status_code, response.text)
        return
    
    data = response.json()
    documentos = data.get("data", {}).get("document_metas", [])

    # Se não houver documentos, ainda adiciona linha no DataFrame
    if not documentos:
        registro.append({
            "banco": projeto_nome,
            "ano": ano,
            "nome": None,
            "data_publicada": None,
            "link": None,
            "trimestre": None

        })
        return

    for doc in documentos:
        file_id = doc.get("id")
        file_name = doc.get("file_name_original", "arquivo")
        file_quarter = doc.get("file_quarter")
        file_year = doc.get("file_year")
        file_url = doc.get("file_url")

        if not file_name.lower().endswith(".pdf"):
            file_name += ".pdf"

        name_file = f"{file_name}_{file_id}.pdf"
        data_publicacao = doc.get("file_published_date")
        trimestre = f"{file_quarter}T{str(file_year)[-2:]}"

        data_publicacao = datetime.fromisoformat(data_publicacao.replace('Z', '+00:00'))

        registro.append({
            "banco": projeto_nome,
            "ano": ano,
            "nome": name_file,
            "data_publicada": data_publicacao,
            "link": file_url,
            "trimestre": trimestre
        })


def main():

    projeto = {
        "nome": "B3",
        "url": "https://apicatalog.mziq.com/filemanager/company/5fd7b7d8-54a1-472d-8426-eb896ad8a3c4/filter/categories/year/meta",
        "categories": ["central_de_resultados_release_de_resultados"],
    }
    
    ano_atual = datetime.now().year
    registro = []

    for ano in range(2008, ano_atual + 1):
        payload = {
            "year": str(ano),
            "categories": projeto["categories"],
            "language": "pt_BR",
        }
        download(projeto["url"], payload, projeto["nome"], ano, registro)
    
    return registro

def insert_date(registro):
    
    df = pd.DataFrame(registro)

    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]

    df['data_existente'] = datetime.now()

    conn = get_connection()
    cur = conn.cursor()

    insert_sql = """INSERT INTO dados (
        id, banco, ano, nome, data_publicada, data_existente, link, trimestre, novo_arquivo
    ) VALUES (
        %(id)s, %(banco)s, %(ano)s, %(nome)s, %(data_publicada)s, %(data_existente)s, %(link)s, %(trimestre)s, TRUE
    )
    ON CONFLICT (banco, nome, data_publicada) DO UPDATE SET
        ano = EXCLUDED.ano,
        data_existente = EXCLUDED.data_existente,
        link = EXCLUDED.link,
        trimestre = EXCLUDED.trimestre,
        novo_arquivo = FALSE;"""


    try:
        execute_batch(cur, insert_sql, df.to_dict("records"))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir dados: {e}")

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    registro = main()
    insert_date(registro)