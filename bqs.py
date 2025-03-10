import urllib.parse
import time
import sys
import os
import warnings
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from dotenv import load_dotenv
from tqdm import tqdm
from helpers import *
from get_data_pw import get_data_pw

# Oculta os warnings
warnings.filterwarnings("ignore")

# Inicializa o contador de tempo
start_time = time.time()

######### CRIAÇÃO DAS PASTAS DE SAÍDA #########
# Diretório base
base_dir = "outputs"

# Subpastas por ano
anos = ["2023", "2024", "2025"]
subpastas = ["entregues", "justificativas", "resumos", "status", "status_det"]

# Criar estrutura de pastas para cada ano
for ano in anos:
    for subpasta in subpastas:
        caminho = os.path.join(base_dir, ano, subpasta)
        os.makedirs(caminho, exist_ok=True)

# Criar estrutura de pastas para "mapas"
mapas_subpastas = ["pizzas"]
for subpasta in mapas_subpastas:
    caminho = os.path.join(base_dir, "mapas", subpasta)
    os.makedirs(caminho, exist_ok=True)

print("Estrutura de diretórios criada com sucesso!")

######### COLETA DOS DADOS DO PROXY E DO .ENV #########

# Carregar variáveis do .env
load_dotenv()
cred_google = os.getenv('GSHEET_CRED')
url_sheet = os.getenv('GSHEET_KEY_SHEET')

# Proxy
usuario = os.getenv('USUARIO_PROXY')
senha_bruta = os.getenv('PASS_PROXY')
senha = urllib.parse.quote(senha_bruta, safe='')
adress = os.getenv('ENDERECO_PROXY')
proxy = [usuario, senha, adress]

######### BUSCA DO DATAFRAME DO PLANINFRAWEB #########
try:
    df = get_data_pw(proxy, cred_google, url_sheet)
except Exception as e:
    print(f"Erro: {e}")
    sys.exit(1)

# Filtrar os dados
df = df[df['INSCRIÇÃO'] != 'Encerrado']  # Filtra os vigentes

# Limpar e converter a coluna VALOR para numérica
df['VALOR'] = df['VALOR'].str.replace('R$ ', '')
df['VALOR'] = df['VALOR'].str.replace('.', '')
df['VALOR'] = df['VALOR'].str.replace(',', '.')
df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
df['Ordem_Status'] = pd.to_numeric(df['Ordem_Status'], errors='coerce')

# Converte datas para formato de datas
df['Data de entrega do Projeto'] = pd.to_datetime(df['Data de entrega do Projeto'],format='%d/%m/%Y')
df['INÍCIO_PTA'] = pd.to_datetime(df['INÍCIO_PTA'],format='%d/%m/%Y')
df['TÉRMINO_PTA'] = pd.to_datetime(df['TÉRMINO_PTA'],format='%d/%m/%Y')
df['PRAZO PROJETO VIGENTE'] = pd.to_datetime(df['PRAZO PROJETO VIGENTE'],format='%d/%m/%Y')
df['Data de entrega do Projeto'] = pd.to_datetime(df['Data de entrega do Projeto'],format='%d/%m/%Y')

# Criar as colunas de cód de status de projeto e de Status de projeto
df['PRAZO PROJETO VIGENTE + PTA'] = df.apply(define_prazo_vigente, axis=1)
df['PRAZO PROJETO VIGENTE + PTA'] = pd.to_datetime(df['PRAZO PROJETO VIGENTE + PTA'])
df['PRAZO PROJETO VIGENTE + PTA'] = df['PRAZO PROJETO VIGENTE + PTA'].dt.date
df['COD_PRAZO_PRJ'] = df.apply(cod_proj, axis=1)
df['STATUS_PRAZO_PRJ'] = df['COD_PRAZO_PRJ'].apply(definir_status_prazo)
df['COD_PRAZO_PRJ'].value_counts() 
df['STATUS_PRAZO_PRJ'].value_counts()
df['PRAZO PRJ'] = df.apply(lambda row: prazo_projeto(row['COD_PRAZO_PRJ'], row['PRAZO PROJETO VIGENTE + PTA']), axis=1)

# Criar a coluna PLANINFRA
df['PLANINFRA'] = df.apply(define_planinfra, axis=1)

######### GERAÇÃO DOS RESUMOS #########
df_2023 = df[df['PLANINFRA'] == 'PLANINFRA 2023/2024']  # Filtra pelo PLANINFRA 2023_2024
img_resumo_23_24 = criar_resumo(df_2023,'2023','resumo_23_24','RESUMO 2023/2024')
df_2024 = df[df['PLANINFRA'] == 'PLANINFRA 2024/2025']  # Filtra pelo PLANINFRA 2024_2025
img_resumo_24_25 = criar_resumo(df_2024,'2024','resumo_24_25','RESUMO 2024/2025')
df_2025 = df[df['PLANINFRA'] == 'PLANINFRA 2025/2026']  # Filtra pelo PLANINFRA 2025_2026
img_resumo_25_26 = criar_resumo(df_2025,'2025','resumo_25_26','RESUMO 2025/2026')
# Itens a serem combinados em um só grupo
grupo_combinado = ['Projeto Concluído (PRC)','Obra Concluída (OBC)*', 'Obra Iniciada (OBI)', 'Licitação Autorizada (LIA)', 'Obra Cancelada com Projeto Concluído (OCN)','Obra Suspensa (OSP)']
lista_status_23_24 = df_2023['STATUS_Ext'].unique().tolist()
# Criando a nova lista com o grupo combinado e os demais itens separados
lista_status_23_24 = [grupo_combinado] + [[item] for item in lista_status_23_24 if item not in grupo_combinado]
img_destaque_2023 = []
for item in lista_status_23_24:
    img_destaque_2023.append(criar_resumo_destaque(df_2023,'2023',f'resumo_23_24_{item[0].replace('(', '').replace(')', '')[-3:]}','RESUMO 2023/2024', item))
lista_status_24_25 = df_2024['STATUS_Ext'].unique().tolist()
# Criando a nova lista com o grupo combinado e os demais itens separados
lista_status_24_25 = [grupo_combinado] + [[item] for item in lista_status_24_25 if item not in grupo_combinado]
img_destaque_2024 = []
for item in lista_status_24_25:
    img_destaque_2024.append(criar_resumo_destaque(df_2024,'2024',f'resumo_24_25_{item[0].replace('(', '').replace(')', '')[-3:]}','RESUMO 2024/2025', item))
#df_2024.to_excel('teste.xlsx', index=False)
#df_2023['STATUS_PRAZO_PRJ'].value_counts() 

lista_status_25_26 = df_2025['STATUS_Ext'].unique().tolist()
# Criando a nova lista com o grupo combinado e os demais itens separados
lista_status_25_26 = [grupo_combinado] + [[item] for item in lista_status_25_26 if item not in grupo_combinado]
img_destaque_2025 = []
for item in lista_status_25_26:
    img_destaque_2025.append(criar_resumo_destaque(df_2025,'2025',f'resumo_25_26_{item[0].replace('(', '').replace(')', '')[-3:]}','RESUMO 2025/2026', item))

######### GERAÇÃO DO GRÁFICO DE BARRAS DOS STATUS #########
img_status_23_24 = criar_barra_status(df_2023,'2023','status_23_24','PLANINFRA 2023/2024')
img_status_24_25 = criar_barra_status(df_2024,'2024','status_24_25','PLANINFRA 2024/2025')
img_status_25_26 = criar_barra_status(df_2025,'2025','status_25_26','PLANINFRA 2025/2026')

######### GERAÇÃO DO GRÁFICO DE BARRAS DOS STATUS DE PROJETOS AGD #########
df_2023_agd = df_2023[df_2023['STATUS'] == 'AGD']  
img_status_23_24_agd = criar_barra_status_prj(df_2023_agd,'2023','status_23_24_agd','PLANINFRA AGD 2023/2024')
df_2024_agd = df_2024[df_2024['STATUS'] == 'AGD']
img_status_24_25_agd = criar_barra_status_prj(df_2024_agd,'2024','status_24_25_agd','PLANINFRA AGD 2024/2025')
df_2025_agd = df_2025[df_2025['STATUS'] == 'AGD']
img_status_25_26_agd = criar_barra_status_prj(df_2025_agd,'2025','status_25_26_agd','PLANINFRA AGD 2025/2026')

######### GERAÇÃO DO GRÁFICO DE BARRAS DOS STATUS DE PROJETOS PRI #########
df_2023_pri = df_2023[df_2023['STATUS'] == 'PRI']  
img_status_23_24_pri = criar_barra_status_prj(df_2023_pri,'2023','status_23_24_pri','PLANINFRA PRI 2023/2024')
df_2024_pri = df_2024[df_2024['STATUS'] == 'PRI']
img_status_24_25_pri = criar_barra_status_prj(df_2024_pri,'2024','status_24_25_pri','PLANINFRA PRI 2024/2025')
#df_2024_pri.to_excel('teste.xlsx', index=False)
df_2025_pri = df_2025[df_2025['STATUS'] == 'PRI']
img_status_25_26_pri = criar_barra_status_prj(df_2025_pri,'2025','status_25_26_pri','PLANINFRA PRI 2025/2026')

######### GERAÇÃO DO GRÁFICO DE BARRAS DOS PROJETOS ENTREGUES POR ELOS #########
df_2023_prc = df_2023[df_2023['STATUS'].isin(['PRC', 'OBI', 'OBC', 'LIA', 'OSP', 'OCN'])]  
img_prc_2023 = criar_barra_resp_prc(df_2023_prc,'2023', 'resp_23_24_prc', 'Quantidade de projetos concluídos (PRC, LIA, OBI, OBC)')
df_2024_prc = df_2024[df_2024['STATUS'].isin(['PRC', 'OBI', 'OBC', 'LIA', 'OSP', 'OCN'])]  
img_prc_2024 = criar_barra_resp_prc(df_2024_prc,'2024', 'resp_24_25_prc', 'Quantidade de projetos concluídos (PRC, LIA, OBI, OBC)')
df_2025_prc = df_2025[df_2025['STATUS'].isin(['PRC', 'OBI', 'OBC', 'LIA', 'OSP', 'OCN'])]  
img_prc_2025 = criar_barra_resp_prc(df_2025_prc,'2025', 'resp_25_26_prc', 'Quantidade de projetos concluídos (PRC, LIA, OBI, OBC)')

######### GERAÇÃO DO GRÁFICO DE BARRAS DOS PROJETOS ENTREGUES POR ELOS DESTACANDO GRUPOS #########
img_prc_2023_destaq, img_prc_2023_destaq_lista = criar_barra_resp_prc_destaq(df_2023_prc,'2023', 'resp_23_24_prc', 'Quantidade de projetos concluídos (PRC, LIA, OBI, OBC)')
img_prc_2024_destaq, img_prc_2024_destaq_lista = criar_barra_resp_prc_destaq(df_2024_prc,'2024', 'resp_24_25_prc', 'Quantidade de projetos concluídos (PRC, LIA, OBI, OBC)')
img_prc_2025_destaq, img_prc_2025_destaq_lista = criar_barra_resp_prc_destaq(df_2025_prc,'2025', 'resp_25_26_prc', 'Quantidade de projetos concluídos (PRC, LIA, OBI, OBC)')

######### GERAÇÃO DO GRÁFICO FINANCEIRO DE BARRAS DOS PROJETOS ENTREGUES POR ELOS #########
img_prc_2023_fin = criar_barra_resp_prc_fin(df_2023_prc,'2023', 'resp_23_24_prc_fin', 'Volume financeiro de de projetos concluídos (PRC, LIA, OBI, OBC)')
img_prc_2024_fin = criar_barra_resp_prc_fin(df_2024_prc,'2024', 'resp_24_25_prc_fin', 'Volume financeiro de de projetos concluídos (PRC, LIA, OBI, OBC)')
img_prc_2025_fin = criar_barra_resp_prc_fin(df_2025_prc,'2025', 'resp_25_26_prc_fin', 'Volume financeiro de de projetos concluídos (PRC, LIA, OBI, OBC)')

######### GERAÇÃO DO GRÁFICO DE BARRAS DOS PROJETOS PRI E AGD POR ELOS #########
df_prj = df[df['STATUS'].isin(['PRI', 'AGD'])]  
img_prj, pie_prj = criar_barra_resp_prj(df_prj, 'resp_prj', 'Carga de projetos dos elos')
mapa_prj = create_map(pie_prj, 'mapa_prj')

######### GERAÇÃO DO GRÁFICO DE BARRAS DAS OBRAS POR ELOS #########
df_obra = df[df['STATUS'].isin(['OBI', 'OSP'])]  
img_obra, pie_obra = criar_barra_resp_obr(df_obra, 'resp_obra', 'Carga de obra')
mapa_obra = create_map(pie_obra, 'mapa_obra')

######### GERAÇÃO DO GRÁFICO DE BARRAS DAS OBRAS PROSPECTIVAS POR ELOS #########
df['STATUS_amplo'] = np.where(df['STATUS'].isin(['PRI', 'PRC', 'AGD', 'PII']), 'Fase de projeto (AGD, PRI, etc.)', df['STATUS'])
df_prospec = df[df['STATUS'].isin(['AGD', 'PRI', 'PII', 'PRC', 'LIA', 'OBI', 'OSP'])]  
img_prospec, pie_prospec = criar_barra_resp_prospec(df_prospec, 'resp_prospec', 'Carga prospectiva de obra')
mapa_prospec = create_map(pie_prospec, 'mapa_prospec')

######### GERAÇÃO DAS TABELAS DE JUSTIFICATIVAS #########
#2023
df_2023_expirado = df_2023[df_2023['STATUS_PRAZO_PRJ']=='Prazo Expirado']
img_just_expirado = criar_justificativas(df_2023_expirado,'2023', 'justificativas_atrasados_23_24')
df_2023_ausente = df_2023[df_2023['STATUS_PRAZO_PRJ']=='Prazo Ausente']
img_just_ausente = criar_justificativas(df_2023_ausente,'2023', 'justificativas_ausentes_23_24')
df_2023_pta_atr = df_2023[df_2023['STATUS_PRAZO_PRJ']=='Projeto não iniciado (pelo PTA deveria)']
img_just_pta_atr = criar_justificativas(df_2023_pta_atr,'2023', 'justificativas_pta_atr_23_24')
df_2023_encerrando = df_2023[df_2023['STATUS_PRAZO_PRJ']=='Prazo do projeto encerrando (30d)']
img_just_encerrando = criar_justificativas(df_2023_encerrando,'2023', 'justificativas_encerrando_23_24')
df_2023_tep_atr = df_2023[df_2023['STATUS_PRAZO_PRJ']=='TEP não assinado (+30d)']
img_just_tep_atr = criar_justificativas(df_2023_tep_atr,'2023', 'justificativas_tep_atr_23_24')
df_2023_andamento = df_2023[df_2023['STATUS_PRAZO_PRJ']=='Projeto em andamento']
img_just_andamento = criar_justificativas(df_2023_andamento,'2023', 'justificativas_andamento_23_24')
df_2023_aguardando = df_2023[df_2023['STATUS_PRAZO_PRJ']=='Aguardando início de projeto']
img_just_aguardando = criar_justificativas(df_2023_aguardando,'2023', 'justificativas_aguardando_23_24')
df_2023_suspenso = df_2023[df_2023['STATUS']=='PSP']
img_just_suspenso = criar_justificativas(df_2023_suspenso,'2023', 'justificativas_suspenso_23_24')
df_2023_interrompido = df_2023[df_2023['STATUS']=='PII']
img_just_interrompido = criar_justificativas(df_2023_interrompido,'2023', 'justificativas_interrompido_23_24')

#2024
df_2024_expirado = df_2024[df_2024['STATUS_PRAZO_PRJ']=='Prazo Expirado']
img_just_expirado = criar_justificativas(df_2024_expirado,'2024', 'justificativas_atrasados_24_25')
df_2024_ausente = df_2024[df_2024['STATUS_PRAZO_PRJ']=='Prazo Ausente']
img_just_ausente = criar_justificativas(df_2024_ausente,'2024', 'justificativas_ausentes_24_25')
df_2024_pta_atr = df_2024[df_2024['STATUS_PRAZO_PRJ']=='Projeto não iniciado (pelo PTA deveria)']
img_just_pta_atr = criar_justificativas(df_2024_pta_atr,'2024', 'justificativas_pta_atr_24_25')
df_2024_encerrando = df_2024[df_2024['STATUS_PRAZO_PRJ']=='Prazo do projeto encerrando (30d)']
img_just_encerrando = criar_justificativas(df_2024_encerrando,'2024', 'justificativas_encerrando_24_25')
df_2024_tep_atr = df_2024[df_2024['STATUS_PRAZO_PRJ']=='TEP não assinado (+30d)']
img_just_tep_atr = criar_justificativas(df_2024_tep_atr,'2024', 'justificativas_tep_atr_24_25')
df_2024_andamento = df_2024[df_2024['STATUS_PRAZO_PRJ']=='Projeto em andamento']
img_just_andamento = criar_justificativas(df_2024_andamento,'2024', 'justificativas_andamento_24_25')
df_2024_aguardando = df_2024[df_2024['STATUS_PRAZO_PRJ']=='Aguardando início de projeto']
img_just_aguardando = criar_justificativas(df_2024_aguardando,'2024', 'justificativas_aguardando_24_25')
df_2024_suspenso = df_2024[df_2024['STATUS']=='PSP']
img_just_suspenso = criar_justificativas(df_2024_suspenso,'2024', 'justificativas_suspenso_24_25')
df_2024_interrompido = df_2024[df_2024['STATUS']=='PII']
img_just_interrompido = criar_justificativas(df_2024_interrompido,'2024', 'justificativas_interrompido_24_25')

#2025
df_2025_expirado = df_2025[df_2025['STATUS_PRAZO_PRJ']=='Prazo Expirado']
img_just_expirado = criar_justificativas(df_2025_expirado,'2025', 'justificativas_atrasados_25_26')
df_2025_ausente = df_2025[df_2025['STATUS_PRAZO_PRJ']=='Prazo Ausente']
img_just_ausente = criar_justificativas(df_2025_ausente,'2025', 'justificativas_ausentes_25_26')
df_2025_pta_atr = df_2025[df_2025['STATUS_PRAZO_PRJ']=='Projeto não iniciado (pelo PTA deveria)']
img_just_pta_atr = criar_justificativas(df_2025_pta_atr,'2025', 'justificativas_pta_atr_25_26')
df_2025_encerrando = df_2025[df_2025['STATUS_PRAZO_PRJ']=='Prazo do projeto encerrando (30d)']
img_just_encerrando = criar_justificativas(df_2025_encerrando,'2025', 'justificativas_encerrando_25_26')
df_2025_tep_atr = df_2025[df_2025['STATUS_PRAZO_PRJ']=='TEP não assinado (+30d)']
img_just_tep_atr = criar_justificativas(df_2025_tep_atr,'2025', 'justificativas_tep_atr_25_26')
df_2025_andamento = df_2025[df_2025['STATUS_PRAZO_PRJ']=='Projeto em andamento']
img_just_andamento = criar_justificativas(df_2025_andamento,'2025', 'justificativas_andamento_25_26')
df_2025_aguardando = df_2025[df_2025['STATUS_PRAZO_PRJ']=='Aguardando início de projeto']
img_just_aguardando = criar_justificativas(df_2025_aguardando,'2025', 'justificativas_aguardando_25_26')
df_2025_suspenso = df_2025[df_2025['STATUS']=='PSP']
img_just_suspenso = criar_justificativas(df_2025_suspenso,'2025', 'justificativas_suspenso_25_26')
df_2025_interrompido = df_2025[df_2025['STATUS']=='PII']
img_just_interrompido = criar_justificativas(df_2025_interrompido,'2025', 'justificativas_interrompido_25_26')

print("Gráficos gerados com sucesso.")