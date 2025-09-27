# 📊 Painel de EBITDA – 2008 a 2025  

Este projeto coleta, processa e exibe de forma interativa os valores de **EBITDA** de 2008 até 2025, utilizando **Python**, **PostgreSQL** e um **painel em Streamlit** hospedado no **Render**.  

Link para acesso: https://projeto-b3.onrender.com/

---

## 🏦 O que é EBITDA?  

O **EBITDA** (*Earnings Before Interest, Taxes, Depreciation and Amortization*) é um indicador financeiro que mede o **resultado operacional de uma empresa antes dos efeitos de:**

- **Juros** (*Interest*)  
- **Impostos** (*Taxes*)  
- **Depreciação** (*Depreciation*)  
- **Amortização** (*Amortization*)  

👉 Em português, é conhecido como **LAJIDA** (*Lucros Antes de Juros, Impostos, Depreciação e Amortização*).  

### 📌 Por que o EBITDA é importante?
- Mostra a **geração de caixa operacional** da empresa.  
- Elimina efeitos de financiamentos, impostos e políticas contábeis.  
- Permite **comparar empresas** e avaliar a **eficiência operacional**.  

---

## ⚙️ Funcionalidades
- 🔄 **Coleta automática** de documentos (PDFs) via API.  
- 🗃️ **Extração de EBITDA** usando expressões regulares (Regex).  
- 🗄️ **Armazenamento no PostgreSQL** em tabelas normalizadas.  
- ✅ **Idempotência**: evita duplicação de registros já existentes.  
- 📈 **Painel interativo em Streamlit**, com:
  - KPIs (último EBITDA, variação QoQ, variação YoY, média do ano).  
  - Evolução histórica (linha temporal 2008–2025).  
  - Barras anuais consolidadas.  
  - Heatmap Ano × Trimestre (sazonalidade).  
  - Ranking dos **Top 5 / Bottom 5 trimestres**.  
  - Tabela detalhada com opção de exportar CSV/Excel.  
- 📝 **Insights automáticos**: geração de comentários dinâmicos.  

---

## 🗄️ Estratégia de Banco de Dados

Durante o desenvolvimento, aplicamos conceitos para manter a base **limpa e eficiente**:

- 🔄 **Idempotência na tabela `dados`**  
  A inserção utiliza `ON CONFLICT` para evitar duplicados, permitindo rodar o processo várias vezes sem retrabalho.  

- 🧩 **Regex na extração de valores para `valores_novo`**  
  PDFs são processados e os valores de **EBITDA** são extraídos com expressões regulares, reduzindo ruído e aumentando a precisão.  

Esse design garante **eficiência**, **consistência** e **agilidade**.  

---

## 📐 Estrutura das Tabelas
### `dados`
| Coluna          | Tipo        | Descrição |
|-----------------|------------|-----------|
| id              | VARCHAR    | Identificador único |
| banco           | VARCHAR    | Nome do banco |
| ano             | BIGINT     | Ano de referência |
| nome            | VARCHAR    | Nome do arquivo PDF |
| trimestre       | VARCHAR    | Ex: 1T25 |
| data_publicada  | TIMESTAMP  | Data de publicação |
| data_existente  | TIMESTAMP  | Data de inserção no BD |
| link            | VARCHAR    | Link para o documento |

### `valores_novo`
| Coluna          | Tipo        | Descrição |
|-----------------|------------|-----------|
| id              | VARCHAR    | Identificador (ligação com `dados`) |
| banco           | VARCHAR    | Nome do banco |
| trimestre       | VARCHAR    | Trimestre (PK junto com id) |
| valores         | DECIMAL    | Valor do EBITDA |
| data_publicada  | TIMESTAMP  | Data de referência |
| data_atualizacao| TIMESTAMP  | Última atualização |

> 🔑 **Chave primária (`PRIMARY KEY`) em `(id, trimestre)` garante unicidade e permite upsert.  

---

## 🖥️ Tecnologias utilizadas
- **Python** (requests, pandas, psycopg2, pypdf, regex)  
- **PostgreSQL** (armazenamento e idempotência com `ON CONFLICT`)  
- **Streamlit** (painel interativo)  
- **Plotly** (gráficos dinâmicos)  
- **Render** (deploy do painel)  

---

## 🚀 Como executar localmente

### 1. Criar ambiente virtual
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

---
```
<h2>📄 Licença</h2>
<p>Este projeto está licenciado sob a <a href="LICENSE">MIT License</a>.</p>
    
<h2>🤝 Contribuição</h2>

<p>Fique à vontade para abrir issues e enviar pull requests para melhorias no projeto!</p>
    
<h2>📞 Contato</h2>
<p>Caso tenha dúvidas ou sugestões, entre em contato:</p>
<ul>
    <li>📧 Email: <a href="mailto:santossilvahenrygabriel58@gmail.com">Meu email de contato</a></li>
    <li>🔗 LinkedIn: <a href="www.linkedin.com/in/henry-gabriel-santos-silva-6ba776209">Meu Perfil linkedin</a></li>
</ul>
    
<hr>
    
<p>⭐ Se gostou do projeto, deixe um star no repositório!</p>