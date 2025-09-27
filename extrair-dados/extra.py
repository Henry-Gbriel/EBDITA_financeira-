import os
import re
import requests
from pypdf import PdfReader, PdfWriter
import pandas as pd
from datetime import datetime
from decimal import Decimal
from config import POSTGRES_CONFIG
import psycopg2
from psycopg2.extras import execute_batch
import shutil
import uuid

nome_banco = 'B3'
pasta_download = "downloads_B3"
os.makedirs(pasta_download, exist_ok=True)  # cria a pasta se não existir


# Conexão PostgreSQL
def get_connection():
    return psycopg2.connect(
        host=POSTGRES_CONFIG['host'],
        port=POSTGRES_CONFIG['port'],
        user=POSTGRES_CONFIG['user'],
        password=POSTGRES_CONFIG['password'],
        dbname=POSTGRES_CONFIG['database'],
        sslmode="require"
    )


# Download dos PDFs
def baixar_pdf(url, nome_arquivo):
    caminho = os.path.join(pasta_download, nome_arquivo)
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        with open(caminho, "wb") as f:
            f.write(resp.content)
        return caminho
    except Exception as e:
        print(f"Erro ao baixar {nome_arquivo}: {e}")
        return None


# Busca PDFs que ainda não foram processados (novo_arquivo = TRUE)
def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, banco, link, nome, data_publicada, trimestre
        FROM dados
        WHERE novo_arquivo = TRUE AND banco = %s
    """, (nome_banco,))
    rows = cur.fetchall()

    docs = []
    for row in rows:
        doc = {
            "id": row[0],
            "banco": row[1],
            "link": row[2],
            "nome": row[3],
            "data_publicada": row[4],
            "trimestre": row[5],
        }
        doc["path"] = baixar_pdf(doc["link"], doc["nome"])
        docs.append(doc)

    cur.close()
    conn.close()
    return docs


# Limpeza de PDF (filtra páginas que contenham certas palavras)
def limpe_pdf(caminho_arquivo, nome_arquivo):
    search_texts = ["EBDITA", "EBITDA recorrente"]
    try:
        with open(caminho_arquivo, 'rb') as file:
            reader = PdfReader(file)
            writer = PdfWriter()
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text() or ""
                    if any(term.lower() in text.lower() for term in search_texts):
                        writer.add_page(page)
                except Exception as e:
                    print(f"[ERRO] Falha na página {i + 1}: {e}")
            if writer.pages:
                with open(caminho_arquivo, 'wb') as temp_file:
                    writer.write(temp_file)
            else:
                print("Nenhuma página contendo as palavras-chave foi encontrada.")
    except Exception as e:
        print(f"[ERRO] Não foi possível processar o arquivo {nome_arquivo}: {e}")


# Processa PDFs, extrai EBITDA e salva no Postgres
def search(docs_info):
    conn = get_connection()
    cur = conn.cursor()

    insert_sql = """
    INSERT INTO valores_novo (
        id, banco, trimestre, valores, data_publicada, data_atualizacao
    )
    VALUES (
        %(id)s, %(banco)s, %(trimestre)s, %(valores)s, %(data_publicada)s, NOW()
    )
    ON CONFLICT (id, trimestre)
    DO UPDATE SET
        banco = EXCLUDED.banco,
        valores = EXCLUDED.valores,
        data_publicada = EXCLUDED.data_publicada,
        data_atualizacao = NOW();
    """


    try:
        registros = []
        for doc in docs_info:
            if not doc["path"]:
                continue  # pular arquivos que não foram baixados

            try:
                text = ""
                reader = PdfReader(doc["path"])
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + " "

                # Regex para capturar EBITDA
                match = re.search(r"EBITDA\s+([\d\.,]+)", text)
                valor = Decimal(match.group(1).replace(".", "").replace(",", ".")) * Decimal("1000000") if match else Decimal("0.0")

                registros.append({
                    "id": doc["id"],
                    "banco": doc["banco"],
                    "valores": valor,
                    "data_publicada": doc["data_publicada"],
                    "trimestre": doc["trimestre"],
                    "data_atualizacao": datetime.now(),
                })

            except Exception as e:
                print(f"Erro ao processar {doc['id']}: {e}")

        if registros:
            execute_batch(cur, insert_sql, registros)
            conn.commit()
            print("Valores inseridos/atualizados com sucesso!")

    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir valores: {e}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    docs = main()
    if docs:
        search(docs)

    # Excluir a pasta de PDFs após o processamento
    if os.path.exists(pasta_download):
        shutil.rmtree(pasta_download)
        print(f"Pasta '{pasta_download}' excluída após o processamento.")
