
create database B3_dados;

CREATE TABLE dados (
    id VARCHAR(300) PRIMARY KEY,
    banco VARCHAR(100),
    trimestre VARCHAR(10),
    nome TEXT,
    link TEXT,
    novo_arquivo BOOLEAN,
    ano INT,
    data_publicada TIMESTAMP,
    data_existente TIMESTAMP
);


CREATE TABLE valores(
    id VARCHAR(300) NOT NULL,
    banco VARCHAR(300),
    trimestre VARCHAR(10) NOT NULL,
    valores DECIMAL(18,2),
    data_publicada TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valores_novo_pk PRIMARY KEY (id, trimestre)
);


--ALTER TABLE dados ADD PRIMARY KEY (id);

--ALTER TABLE dados ADD CONSTRAINT unique_link UNIQUE(link);


ALTER TABLE dados
ADD CONSTRAINT unique_banco_nome_data_publicada UNIQUE (banco, nome, data_publicada);

ALTER TABLE valores ADD CONSTRAINT valores_pkey PRIMARY KEY (id);

ALTER TABLE valores ADD CONSTRAINT valores_unique UNIQUE (id, trimestre);

--- B3 - Resultados de 2012
INSERT INTO dados (id, banco, trimestre, nome, link, ano, data_publicada, data_existente,novo_arquivo)
VALUES ('3903196b-5ff7-4a92-b10a-e0546f827481-2T', 'B3', '2T12', 'EarningsRelease2t12.pdf', 'https://api.mziq.com/mzfilemanager/d/5fd7b7d8-54a1-472d-8426-eb896ad8a3c4/4d033510-02f3-4443-ab87-d75fb9166d20?origin=1', '2012', '2012-06-30T00:00:00.000Z' ,'2025-09-26 13:32:17.245255', 'TRUE');

INSERT INTO dados (id, banco, trimestre, nome, link, ano, data_publicada, data_existente,novo_arquivo)
VALUES ('3903196b-5ff7-4a92-b10a-e0546f827481-3T', 'B3', '3T12', 'EarningsRelease2t13.pdf', 'https://api.mziq.com/mzfilemanager/d/5fd7b7d8-54a1-472d-8426-eb896ad8a3c4/3031cbe8-5e42-4ebf-bfc5-3f0bd49c85e5?origin=1', '2012', '2012-09-30T00:00:00.000Z' ,'2025-09-26 13:32:17.245255', 'TRUE');

INSERT INTO dados (id, banco, trimestre, nome, link, ano, data_publicada, data_existente,novo_arquivo)
VALUES ('3903196b-5ff7-4a92-b10a-e0546f827481-4T', 'B3', '4T12', 'EarningsRelease2t14.pdf', 'https://api.mziq.com/mzfilemanager/d/5fd7b7d8-54a1-472d-8426-eb896ad8a3c4/73edd98b-450d-4297-b43b-944b0b9a65e3?origin=1', '2012', '2012-12-31T00:00:00.000Z' ,'2025-09-26 13:32:17.245255', 'TRUE');

UPDATE cdp_prd.poupanca.valores
SET valores = '267001000.00'
WHERE id = '3903196b-5ff7-4a92-b10a-e0546f827481-4T'; 
------------

drop table valores;