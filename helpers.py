import pandas as pd
import urllib.parse
import numpy as np
import imgkit
import os 
import html
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from PIL import Image

def define_planinfra(row):
    if '2024/2025' in row['INSCRIÇÃO']:
        return 'PLANINFRA 2024/2025'
    elif '2023/2024' in row['INSCRIÇÃO']:
        return 'PLANINFRA 2023/2024'
    elif '2025/2026' in row['INSCRIÇÃO']:
        return 'PLANINFRA 2025/2026'
    else:
        return 'Anterior a 2023'

def define_prazo_vigente(row):
    if pd.isna(row['PRAZO PROJETO VIGENTE']) and not pd.isna(row['TÉRMINO_PTA']):
        return row['TÉRMINO_PTA']
    elif pd.isna(row['TÉRMINO_PTA']):
        # return today date
        return datetime.today().date()
    else:
        return row['PRAZO PROJETO VIGENTE']
    
def cod_proj(row):
    if row['STATUS'] in ['PCN', 'PSP', 'PII']:
        return 9
    elif row['STATUS'] in ['PRC', 'LIA', 'OBI', 'OBC', 'OSP', 'OCN']:
        if pd.isna(row['PRAZO PROJETO VIGENTE + PTA']):
            return 8
        else:
            return 7
    elif row['STATUS'] == 'PRI':
        if row['Data de entrega do Projeto'] + timedelta(days=30) < (datetime.today() - timedelta(days=1)):
            return 4
        elif row['PRAZO PROJETO VIGENTE + PTA'] < (datetime.today().date() -timedelta(days=1)) and pd.isna(row['Data de entrega do Projeto']):
            return 1
        elif row['PRAZO PROJETO VIGENTE + PTA'] < datetime.today().date() + timedelta(days=29):
            return 3
        else:
            return 5
    elif row['STATUS'] == 'AGD':
        if row['INÍCIO_PTA'] < datetime.today():
            return 2
        else:
            return 6
    else:
        return 9
            
def definir_status_prazo(cod_prazo_prj):
    if cod_prazo_prj == 0:
        return "Prazo Ausente"
    elif cod_prazo_prj == 1:
        return "Prazo Expirado"
    elif cod_prazo_prj == 2:
        return "Projeto não iniciado (pelo PTA deveria)"
    elif cod_prazo_prj == 3:
        return "Prazo do projeto encerrando (30d)"
    elif cod_prazo_prj == 4:
        return "TEP não assinado (+30d)"
    elif cod_prazo_prj == 5:
        return "Projeto em andamento"
    elif cod_prazo_prj == 6:
        return "Aguardando início de projeto"
    elif cod_prazo_prj == 7 or cod_prazo_prj == 8:
        return "Projeto concluído"
    else:
        return "Projeto cancelado ou suspenso"

def prazo_projeto(cod_prazo_prj, prazo_vigente):    
    if cod_prazo_prj == 0:
        return "💥"
    elif cod_prazo_prj == 1:
        return f"💥 {prazo_vigente}"
    elif cod_prazo_prj == 2:
        return f"🔴 {prazo_vigente}"
    elif cod_prazo_prj == 3:
        return f"⚠️ {prazo_vigente}"
    elif cod_prazo_prj == 4:
        return f"🟡 {prazo_vigente}"
    elif cod_prazo_prj == 5:
        return f"📈 {prazo_vigente}"
    elif cod_prazo_prj == 6:
        return f"⏳ {prazo_vigente}"
    elif cod_prazo_prj == 7:
        return f"✅ {prazo_vigente}"
    elif cod_prazo_prj == 8:
        return "✅"
    else:
        return "⛔"

#### TABELAS DE RESUMO ####
def criar_resumo(df, year, filename, title):
    # Contar quantas vezes cada status aparece
    status_count = df.groupby('STATUS_Ext').size().reset_index(name='Quantidade')

    # Somar os valores da coluna VALOR agrupados por Status_ext
    status_sum = df.groupby('STATUS_Ext')['VALOR'].sum().reset_index(name='Total Valor (R$)')
    custo_total = round(status_sum['Total Valor (R$)'].sum()/1000000,2)
    status_sum['Total Valor (R$)'] = status_sum['Total Valor (R$)'].round(2)

    # Juntar as duas informações em um único DataFrame
    summary_df = pd.merge(status_count, status_sum, on='STATUS_Ext')

    # Adicionar a coluna 'Ordem_Status' ao summary_df
    summary_df = pd.merge(summary_df, df[['STATUS_Ext', 'Ordem_Status']], on='STATUS_Ext', how='left')

    # Remover duplicatas da coluna 'Ordem_Status'
    summary_df = summary_df.drop_duplicates(subset='STATUS_Ext')

    # Formatar a coluna 'Total Valor (R$)' no formato brasileiro
    summary_df['Total Valor (R$)'] = summary_df['Total Valor (R$)'].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    # Ordenar o DataFrame pelo campo 'Ordem_Status'
    summary_df = summary_df.sort_values(by='Ordem_Status')
    summary_df = summary_df.drop(columns=['Ordem_Status'])

    # Geração do HTML com estilos

    # Definindo estilo CSS para bordas, alinhamento e cores
    style = """
    <style>
        body {
            font-family: Arial, sans-serif;  /* Fonte Arial para todo o conteúdo */
            font-size: 14px;
        }
        /* Estilo para a tabela de cabeçalho (sem bordas) */
        .header-table {
            width: 100%;
            margin-bottom: 5px;
            border-collapse: collapse;
            font-weight: bold;
            font-family: Arial, sans-serif;
            font-size: 18px;
        }
        .header-table td {
            border: none;
            padding: 4px;
            text-align: right;
        }
        .header-table td:first-child {
                text-align: left;
            }    

        /* Estilo para a tabela principal */
        .main-table {
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            font-size: 14px;
        }
        .main-table th, td {
            padding: 8px;
            border-top: 2px solid black;  /* Borda superior para todas as células */
            border-bottom: 2px solid black;  /* Borda inferior para todas as células */
        }
        .main-table td:first-child {
            border-left: 2px solid black;  /* Borda esquerda para a primeira coluna */
            text-align: left;
            width: 150px;  /* Largura fixa para a primeira coluna */
        }
        .main-table td:last-child {
            border-right: 2px solid black;  /* Borda direita para a última coluna */
            text-align: right;
            width: 60px;  /* Largura fixa para a última coluna */
        }
        .main-table td:nth-child(2) {
            text-align: right;
            width: 30px;  /* Largura fixa para a segunda coluna */
        }
        .main-table tr:nth-child(even) {
            background-color: #bbdefb;  /* Fundo para linhas pares */
        }
        .main-table tr:nth-child(odd) {
            background-color: white;  /* Fundo para linhas ímpares */
        }

        .footer-text {
            font-size: 12px;
            margin-top: 5px;
            text-align: left;
        }
    </style>
    """

    # Criando a tabela adicional com 3 colunas e 1 linha, sem bordas
    qtde = summary_df['Quantidade'].sum()
    header = f"""
    <table class="header-table">
        <tr>
            <td>{title}</td>
            <td>Total: {qtde}</td>
            <td>R$ {custo_total} Mi</td>
        </tr>
    </table>
    """

    # Texto abaixo da tabela
    footer_text = '<div class="footer-text">*Obras concluídas, com emissão do TERD, no ano vigente</div>'

    # Convertendo o DataFrame para HTML e aplicando o estilo
    html_table = summary_df.to_html(index=False, header=False, border=0, classes='main-table')

    # Combinando o estilo e a tabela HTML
    html_output = f"{style}\n{header}\n{html_table}\n{footer_text}"

    # Salvando a tabela como arquivo HTML
    html_path = 'tabela_resumo.html'
    with open('tabela_resumo.html', 'w', encoding='utf-8') as f:
        f.write(html_output)

    # Configurações para gerar a imagem
    img_options = {
        'format': 'png',
        'encoding': 'UTF-8',
        'width': 500 
    }

    # Converter o HTML em imagem (PNG)
    img_output = f'outputs/{year}/resumos/{filename}.png'
    imgkit.from_file(html_path, img_output, options=img_options)

    # Excluir o arquivo HTML após gerar a imagem
    if os.path.exists(html_path):
        os.remove(html_path)
        print(f"Arquivo HTML '{html_path}' excluído com sucesso.")

    return img_output

def adicionar_estilo(row, destaque):
    # Se o STATUS_Ext for 'destaque', aplicar estilo de destaque
    estilo = 'highlight' if row['STATUS_Ext'] in destaque else 'normal'
    # Criar a linha da tabela HTML com a classe correspondente
    return f'<tr class="{estilo}">' + ''.join([f'<td>{cell}</td>' for cell in row]) + '</tr>'

def criar_resumo_destaque(df, year, filename, title,destaque):
    # Contar quantas vezes cada status aparece
    status_count = df.groupby('STATUS_Ext').size().reset_index(name='Quantidade')

    # Somar os valores da coluna VALOR agrupados por Status_ext
    status_sum = df.groupby('STATUS_Ext')['VALOR'].sum().reset_index(name='Total Valor (R$)')
    custo_total = round(status_sum['Total Valor (R$)'].sum()/1000000,2)
    status_sum['Total Valor (R$)'] = status_sum['Total Valor (R$)'].round(2)

    # Juntar as duas informações em um único DataFrame
    summary_df = pd.merge(status_count, status_sum, on='STATUS_Ext')

    # Adicionar a coluna 'Ordem_Status' ao summary_df
    summary_df = pd.merge(summary_df, df[['STATUS_Ext', 'Ordem_Status']], on='STATUS_Ext', how='left')

    # Remover duplicatas da coluna 'Ordem_Status'
    summary_df = summary_df.drop_duplicates(subset='STATUS_Ext')

    # Formatar a coluna 'Total Valor (R$)' no formato brasileiro
    summary_df['Total Valor (R$)'] = summary_df['Total Valor (R$)'].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    # Ordenar o DataFrame pelo campo 'Ordem_Status'
    summary_df = summary_df.sort_values(by='Ordem_Status')
    summary_df = summary_df.drop(columns=['Ordem_Status'])

    # Geração do HTML com estilos

    # Definindo estilo CSS para bordas, alinhamento e cores
    style = """
    <style>
        body {
            font-family: Arial, sans-serif;  /* Fonte Arial para todo o conteúdo */
            font-size: 14px;
        }
        /* Estilo para a tabela de cabeçalho (sem bordas) */
        .header-table {
            width: 100%;
            margin-bottom: 5px;
            border-collapse: collapse;
            font-weight: bold;
            font-family: Arial, sans-serif;
            font-size: 18px;
        }
        .header-table td {
            border: none;
            padding: 4px;
            text-align: right;
        }
        .header-table td:first-child {
                text-align: left;
            }    

        /* Estilo para a tabela principal */
        .main-table {
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            font-size: 14px;
        }
        .main-table th, td {
            padding: 8px;
            border-top: 2px solid black;  /* Borda superior para todas as células */
            border-bottom: 2px solid black;  /* Borda inferior para todas as células */
        }
        .main-table td:first-child {
            border-left: 2px solid black;  /* Borda esquerda para a primeira coluna */
            text-align: left;
            width: 150px;  /* Largura fixa para a primeira coluna */
        }
        .main-table td:last-child {
            border-right: 2px solid black;  /* Borda direita para a última coluna */
            text-align: right;
            width: 60px;  /* Largura fixa para a última coluna */
        }
        .main-table td:nth-child(2) {
            text-align: right;
            width: 30px;  /* Largura fixa para a segunda coluna */
        }
        .main-table tr:nth-child(even) {
            background-color: #bbdefb;  /* Fundo para linhas pares */
        }
        .main-table tr:nth-child(odd) {
            background-color: white;  /* Fundo para linhas ímpares */
        }

        .footer-text {
            font-size: 12px;
            margin-top: 5px;
            text-align: left;
        }

        .highlight {
            font-weight: bold;
            color: black;
        }
        .normal {
            font-style: italic;
            color: gray;
        }
    </style>
    """

    # Criando a tabela adicional com 3 colunas e 1 linha, sem bordas
    qtde = summary_df['Quantidade'].sum()
    header = f"""
    <table class="header-table">
        <tr>
            <td>{title}</td>
            <td>Total: {qtde}</td>
            <td>R$ {custo_total} Mi</td>
        </tr>
    </table>
    """

    # Texto abaixo da tabela
    footer_text = '<div class="footer-text">*Obras concluídas, com emissão do TERD, no ano vigente</div>'

    # Criar as linhas da tabela com o estilo condicional
    html_linhas = '\n'.join([adicionar_estilo(row, destaque) for _, row in summary_df.iterrows()])

    # Definindo a tabela HTML com as classes de estilo
    html_table = f"""
    <table class="main-table">
        {html_linhas}
    </table>
    """

    # Combinando o estilo e a tabela HTML
    html_output = f"{style}\n{header}\n{html_table}\n{footer_text}"

    # Salvando a tabela como arquivo HTML
    html_path = 'tabela_resumo.html'
    with open('tabela_resumo.html', 'w', encoding='utf-8') as f:
        f.write(html_output)

    # Configurações para gerar a imagem
    img_options = {
        'format': 'png',
        'encoding': 'UTF-8',
        'width': 500 
    }

    # Converter o HTML em imagem (PNG)
    img_output = f'outputs/{year}/resumos/{filename}.png'
    imgkit.from_file(html_path, img_output, options=img_options)

    # Excluir o arquivo HTML após gerar a imagem
    if os.path.exists(html_path):
        os.remove(html_path)
        print(f"Arquivo HTML '{html_path}' excluído com sucesso.")

    return img_output

#### GRÁFICO DE BARRAS DE STATUS ####
def criar_barra_status(df, year, filename, title):
    # Agrupar os dados pela coluna 'STATUS' e contar as ocorrências
    status_counts = df['STATUS'].value_counts()

    #Ordenar o status_counts de acordo com a coluna 'ORdem_status'
    df_sorted = df.drop_duplicates('STATUS').set_index('STATUS').loc[status_counts.index]
    status_counts = status_counts.loc[df_sorted.sort_values('Ordem_Status').index]

    # Configurar a fonte para Arial
    plt.rcParams['font.family'] = 'Arial'

    # Criar o gráfico de barras
    plt.figure(figsize=(10, 6))

    # Definir cores para as barras
    colors = ['gray' if status not in ['PRC', 'OBI', 'OBC', 'LIA', 'OSP', 'OCN'] else '#224b89' for status in status_counts.index]

    # Adicionar as barras sem criar uma legenda automática
    bars = plt.bar(status_counts.index, status_counts.values, color=colors)

    # Remover os eixos e bordas
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)

    # Remover as linhas que unem os rótulos do eixo x às barras
    plt.gca().xaxis.tick_bottom()
    plt.gca().tick_params(axis='x', length=0)

    # Definir os rótulos do eixo x na horizontal
    plt.xticks(rotation=0, fontsize=16, fontweight='bold')

    # Remover rótulos do eixo y
    plt.yticks([])

    # Adicionar rótulos de valores acima das barras
    for bar in bars:
        plt.annotate(f'{bar.get_height()}', 
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()), 
                    ha='center', va='bottom', fontsize=16, fontweight='bold')

    # Adicionar uma linha fina preta como eixo x
    plt.axhline(y=0, color='black', linewidth=2)

    # Adicionar a legenda personalizada
    plt.scatter([], [], color='#224b89', label='Projetos entregues')
    plt.legend(loc='upper center', fontsize=16, frameon=False, borderpad=1, bbox_to_anchor=(0.5, -0.1), ncol = 1)

    plt.title(title, fontsize=18, fontweight='bold')

     # Ajustar o layout para deixar espaço para a legenda abaixo
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)  # Aumenta o espaçamento inferior

    img_output = f'outputs/{year}/status/{filename}.png'

    # Salvar o gráfico como imagem
    plt.savefig(img_output, dpi=300, bbox_inches='tight')  # Salva como PNG
    
    #plt.show()
    return img_output

#### GRÁFICO DE BARRAS DE STATUS DE PROJETO PRI OU AGD ####
def criar_barra_status_prj(df, year, filename, title):
    # Agrupar os dados pela coluna 'STATUS_PRAZO_PRJ' e contar as ocorrências
    status_counts = df['STATUS_PRAZO_PRJ'].value_counts()

    # Criar o gráfico de barras
    # Configurar a fonte para Arial
    # Configurar a fonte para Arial
    plt.rcParams['font.family'] = 'Arial'

    # Criar o gráfico de barras
    plt.figure(figsize=(10, 6))

    # Definir cores para as barras
    colors = '#224b89'

    # Adicionar as barras sem criar uma legenda automática
    bars = plt.bar(status_counts.index, status_counts.values, color=colors)

    # Remover os eixos e bordas
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)

    # Remover as linhas que unem os rótulos do eixo x às barras
    plt.gca().xaxis.tick_bottom()
    plt.gca().tick_params(axis='x', length=0)

    # Definir os rótulos do eixo x na horizontal
    plt.xticks(rotation=0, fontsize=10, fontweight='bold')

    # Remover rótulos do eixo y
    plt.yticks([])

    # Adicionar rótulos de valores acima das barras
    for bar in bars:
        plt.annotate(f'{bar.get_height()}', 
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()), 
                    ha='center', va='bottom', fontsize=16, fontweight='bold')

    # Adicionar uma linha fina preta como eixo x
    plt.axhline(y=0, color='black', linewidth=2)

    plt.title(title, fontsize=18, fontweight='bold')
    
    plt.tight_layout()
    img_output = f'outputs/{year}/status_det/{filename}.png'

    # Salvar o gráfico como imagem
    plt.savefig(img_output, dpi=300, bbox_inches='tight')  # Salva como PNG
    
    #plt.show()
    return img_output

#### GRÁFICO DE BARRAS DE PROJETOS ENTREGUES POR ELOS ####
def criar_barra_resp_prc(df, year, filename, title):

    # Substituir os valores que não estão na lista por 'OUTROS'
    lista_inclusao = ['CEPE','SR-BE', 'SR-BR','SR-CO','SR-MN','SR-NT','SR-RJ','SR-SJ','GAC-AN','COMARA','GECAMP']
    df['RESP_PRJ_Abr'] = df['RESP_PRJ_Abr'].where(df['RESP_PRJ_Abr'].isin(lista_inclusao), 'OUTROS')
    
    # Agrupar os dados pela coluna 'STATUS' e contar as ocorrências
    counts = df['RESP_PRJ_Abr'].value_counts()
        
    # Reordenar o DataFrame agrupado com base no total de observações, em ordem decrescente
    counts = counts.loc[counts.sort_values(ascending=False).index]

    # Garantir que 'OUTROS' esteja na última posição
    if 'OUTROS' in counts.index:
        outros = counts.loc[['OUTROS']]
        counts = counts.drop('OUTROS')
        counts = pd.concat([counts, outros])

    # Configurar a fonte para Arial
    plt.rcParams['font.family'] = 'Arial'

    # Criar o gráfico de barras
    plt.figure(figsize=(10, 6))

    # Definir cores para as barras
    #colors = ['gray' if status not in ['PRC', 'OBI', 'OBC', 'LIA', 'OSP', 'OCN'] else '#224b89' for status in status_counts.index]
    colors = '#224b89'

    # Adicionar as barras sem criar uma legenda automática
    bars = plt.bar(counts.index, counts.values, color=colors)

    # Remover os eixos e bordas
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)

    # Remover as linhas que unem os rótulos do eixo x às barras
    plt.gca().xaxis.tick_bottom()
    plt.gca().tick_params(axis='x', length=0)

    # Definir os rótulos do eixo x na horizontal
    plt.xticks(rotation=0, fontsize=12, fontweight='bold')

    # Remover rótulos do eixo y
    plt.yticks([])

    # Adicionar rótulos de valores acima das barras
    for bar in bars:
        plt.annotate(f'{bar.get_height()}', 
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()), 
                    ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Adicionar uma linha fina preta como eixo x
    plt.axhline(y=0, color='black', linewidth=2)

    plt.title(title, fontsize=18, fontweight='bold')

    plt.tight_layout()

    img_output = f'outputs/{year}/entregues/{filename}.png'

    # Salvar o gráfico como imagem
    plt.savefig(img_output, dpi=300, bbox_inches='tight')  # Salva como PNG
    
    #plt.show()
    return img_output

#### GRÁFICO DE BARRAS DE PROJETOS ENTREGUES POR ELOS DESTACANDO POR GRUPOS ####
def criar_barra_resp_prc_destaq(df, year, filename_base, title_base):

    # Substituir os valores que não estão na lista por 'OUTROS'
    lista_inclusao = ['CEPE','SR-BE', 'SR-BR','SR-CO','SR-MN','SR-NT','SR-RJ','SR-SJ','GAC-AN','COMARA','GECAMP']
    df['RESP_PRJ_Abr'] = df['RESP_PRJ_Abr'].where(df['RESP_PRJ_Abr'].isin(lista_inclusao), 'OUTROS')

    # Agrupar os dados pela coluna 'RESP_PRJ_Abr' e contar as ocorrências
    counts = df['RESP_PRJ_Abr'].value_counts()

    # Reordenar o DataFrame agrupado com base no total de observações, em ordem decrescente
    counts = counts.loc[counts.sort_values(ascending=False).index]

    # Garantir que 'OUTROS' esteja na última posição
    if 'OUTROS' in counts.index:
        outros_value = counts['OUTROS']
        counts = counts.drop('OUTROS')
    else:
        outros_value = None

    # Criar uma lista para armazenar subconjuntos dos dados para os gráficos
    subset_list = []
    subset = []
    total = 0

    # Agrupar valores para que cada subset tenha <= 20 projetos
    for idx, value in counts.items():
        # Se o valor individual ultrapassa 20, adicionar diretamente como um subset único
        if value > 20:
            subset_list.append([(idx, value)])
        else:
            # Caso contrário, agrupar de forma que o total não ultrapasse 20
            if total + value > 20:
                subset_list.append(subset)
                subset = []
                total = 0
            subset.append((idx, value))
            total += value

    # Adicionar o último subset se não estiver vazio
    if subset:
        subset_list.append(subset)

    # Adicionar 'OUTROS' como um gráfico separado, se existir
    if outros_value is not None:
        subset_list.append([('OUTROS', outros_value)])

    # Criar os gráficos de barras
    for i, subset in enumerate(subset_list):
        # Extrair rótulos e valores para o gráfico atual
        labels, values = zip(*subset)

        # Configurar a fonte para Arial
        plt.rcParams['font.family'] = 'Arial'

        # Criar o gráfico de barras
        plt.figure(figsize=(10, 6))

        # Garantir que as cores sejam corretamente aplicadas:
        # 1. Se o subset contém "OUTROS" e ele é o único, ele será cinza.
        # 2. Senão, as barras do subset atual são azuis e as outras são cinza.

        all_labels = list(counts.index) + (['OUTROS'] if outros_value is not None else [])
        all_values = list(counts.values) + ([outros_value] if outros_value is not None else [])

        if 'OUTROS' in labels and len(labels) == 1:
            # "OUTROS" será cinza, os outros serão azuis
            colors = ['lightgray' for label in all_labels[:-1]] + ['#224b89']
        else:
            # As barras no subset atual serão azuis, o resto será cinza
            colors = ['#224b89' if label in labels else 'lightgray' for label in all_labels]

        # Adicionar as barras
        bars = plt.bar(all_labels, all_values, color=colors)

        # Remover os eixos e bordas
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.gca().spines['left'].set_visible(False)
        plt.gca().spines['bottom'].set_visible(False)

        # Remover as linhas que unem os rótulos do eixo x às barras
        plt.gca().xaxis.tick_bottom()
        plt.gca().tick_params(axis='x', length=0)

        # Definir os rótulos do eixo x na horizontal
        plt.xticks(rotation=0, fontsize=12, fontweight='bold')

        # Remover rótulos do eixo y
        plt.yticks([])

        # Adicionar rótulos de valores acima das barras
        for bar in bars:
            plt.annotate(f'{bar.get_height()}', 
                        (bar.get_x() + bar.get_width() / 2, bar.get_height()), 
                        ha='center', va='bottom', fontsize=12, fontweight='bold')

        # Adicionar uma linha fina preta como eixo x
        plt.axhline(y=0, color='black', linewidth=2)

        # Adicionar título personalizado para cada gráfico
        #title = f'{title_base} - Gráfico {i+1}'
        plt.title(title_base, fontsize=18, fontweight='bold')

        plt.tight_layout()

        # Salvar o gráfico como imagem
        img_output = f'outputs/{year}/entregues/{filename_base}_grafico_{i+1}.png'
        plt.savefig(img_output, dpi=300, bbox_inches='tight')  # Salva como PNG

        plt.close()  # Fechar a figura para evitar sobreposição

    #Criar as listas de projetos
    grupos_resp = [[item[0] for item in sublist] for sublist in subset_list]
    i = 0
    saida_lista = []
    for resp in grupos_resp:
        img_output = f'outputs/{year}/entregues/{filename_base}_lista_{i+1}.png'
        saida_lista.append(img_output)
        df_tmp = df[df['RESP_PRJ_Abr'].isin(resp)]
        criar_lista_entregues(df_tmp,img_output)
        i += 1

    return [f'outputs/{year}/entregues/{filename_base}_grafico_{i+1}.png' for i in range(len(subset_list))], saida_lista
    
#### GRÁFICO FINANCEIRO DE BARRAS DE PROJETOS ENTREGUES POR ELOS ####
def criar_barra_resp_prc_fin(df, year, filename, title):

    # Substituir os valores que não estão na lista por 'OUTROS'
    lista_inclusao = ['CEPE','SR-BE', 'SR-BR','SR-CO','SR-MN','SR-NT','SR-RJ','SR-SJ','GAC-AN','COMARA','GECAMP']
    df['RESP_PRJ_Abr'] = df['RESP_PRJ_Abr'].where(df['RESP_PRJ_Abr'].isin(lista_inclusao), 'OUTROS')
    
    # Agrupar os dados pela coluna 'RESP_PROJ_Abr' e somar a coluna 'VALOR'
    amounts = df[['VALOR','RESP_PRJ_Abr']].groupby('RESP_PRJ_Abr').sum()
        
    # Reordenar o DataFrame agrupado com base no valor dos projetos, em ordem decrescente
    amounts = amounts.loc[amounts.sort_values(by='VALOR',ascending=False).index]

    # Garantir que 'OUTROS' esteja na última posição
    if 'OUTROS' in amounts.index:
        outros = amounts.loc[['OUTROS']]
        amounts = amounts.drop('OUTROS')
        amounts = pd.concat([amounts, outros])

    # Configurar a fonte para Arial
    plt.rcParams['font.family'] = 'Arial'

    # Criar o gráfico de barras
    plt.figure(figsize=(10, 6))

    # Definir cores para as barras
    #colors = ['gray' if status not in ['PRC', 'OBI', 'OBC', 'LIA', 'OSP', 'OCN'] else '#224b89' for status in status_counts.index]
    colors = '#224b89'

    # Adicionar as barras sem criar uma legenda automática
    bars = plt.bar(amounts.index, amounts['VALOR'], color=colors)

    # Remover os eixos e bordas
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)

    # Remover as linhas que unem os rótulos do eixo x às barras
    plt.gca().xaxis.tick_bottom()
    plt.gca().tick_params(axis='x', length=0)

    # Definir os rótulos do eixo x na horizontal
    plt.xticks(rotation=0, fontsize=12, fontweight='bold')

    # Remover rótulos do eixo y
    plt.yticks([])

    # Adicionar rótulos de valores acima das barras
    for bar in bars:
        valor_milhoes = bar.get_height()/1000000
        plt.annotate(f'R$ {valor_milhoes:.1f}Mi', 
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()), 
                    ha='center', va='bottom', fontsize=12, fontweight='bold')

    # Adicionar uma linha fina preta como eixo x
    plt.axhline(y=0, color='black', linewidth=2)

    plt.title(title, fontsize=18, fontweight='bold')

    plt.tight_layout()

    img_output = f'outputs/{year}/entregues/{filename}.png'

    # Salvar o gráfico como imagem
    plt.savefig(img_output, dpi=300, bbox_inches='tight')  # Salva como PNG
    
    #plt.show()
    return img_output

#### GRÁFICO DE BARRAS DE PROJETOS PRI E AGD POR ELOS ####
def criar_barra_resp_prj(df, filename, title):
    # Substituir os valores que não estão na lista por 'OUTROS'
    lista_inclusao = ['CEPE','SR-BE', 'SR-BR','SR-CO','SR-MN','SR-NT','SR-RJ','SR-SJ','GAC-AN','COMARA','GECAMP']
    df['RESP_PRJ_Abr'] = df['RESP_PRJ_Abr'].where(df['RESP_PRJ_Abr'].isin(lista_inclusao), 'OUTROS')
    
    # Agrupar os dados pela coluna 'STATUS' e contar as ocorrências
    grouped = df.groupby(['RESP_PRJ_Abr','STATUS']).size().unstack(fill_value=0)
    
    # Calcular o total de observações para cada valor de 'RESP_PRJ_Abr'
    total_por_resp = grouped.sum(axis=1)

    # Reordenar o DataFrame agrupado com base no total de observações, em ordem decrescente
    grouped = grouped.loc[total_por_resp.sort_values(ascending=False).index]

    # Garantir que 'OUTROS' esteja na última posição
    if 'OUTROS' in grouped.index:
        outros = grouped.loc[['OUTROS']]
        grouped = grouped.drop('OUTROS')
        grouped = pd.concat([grouped, outros])

    # Configurar a fonte para Arial
    plt.rcParams['font.family'] = 'Arial'

    # Criar o gráfico de barras
    plt.figure(figsize=(10, 6))

    # Definir cores para as barras com base no status
    colors = []
    for status in grouped.columns:
        if status == 'AGD':
            colors.append('gray')  # AGD em cinza
        elif status == 'PRI':
            colors.append('#0072f0')  # PRI em azul
        elif status == 'OBI':
            colors.append('#ff7043')  # OBI em laranja
        elif status == 'OSP':
            colors.append('#f48fb1')  # OBI em rosa
        else:
            colors.append('lightblue')  # Cor padrão para outros status

    # Iniciar a variável de base para empilhamento
    bottom_values = np.zeros(len(grouped))
                             
    # Loop para empilhar as barras de acordo com cada status
    for i, status in enumerate(grouped.columns):
        plt.bar(grouped.index, grouped[status], bottom=bottom_values, label=status, color=colors[i], zorder = 3)
        bottom_values += grouped[status]

    # Remover os eixos e bordas
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)

    # Remover as linhas que unem os rótulos do eixo x às barras
    plt.gca().xaxis.tick_bottom()
    plt.gca().tick_params(axis='x', length=0)
    plt.gca().yaxis.tick_left()
    plt.gca().tick_params(axis='y', length=0)

    # Definir os rótulos do eixo x na horizontal
    plt.xticks(rotation=0, fontsize=12, fontweight='bold')

    # Definir os rótulos do eixo y como inteiros
    # Calcular o valor máximo do eixo Y como o múltiplo de 5 imediatamente superior
    max_value = grouped.sum(axis=1).max()
    max_y = np.ceil(max_value / 5) * 5  # Múltiplo de 5 superior
    plt.yticks(range(0, int(max_y) + 1, 5), fontsize=12)

    # Adicionar linhas de grade horizontais
    plt.grid(axis='y', color='darkgray', linestyle='--', linewidth=0.7, zorder=0)

    # Adicionar a legenda personalizada e posicioná-la abaixo do gráfico
    plt.legend(loc='upper center', fontsize=10, frameon=False, borderpad=1, bbox_to_anchor=(0.5, -0.1), ncol = 2)

    # Adicionar uma linha fina preta como eixo x
    plt.axhline(y=0, color='black', linewidth=2)

    plt.title(title, fontsize=18, fontweight='bold')

    # Ajustar o layout para deixar espaço para a legenda abaixo
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)  # Aumenta o espaçamento inferior

    img_output = f'outputs/mapas/{filename}.png'

    # Salvar o gráfico como imagem
    plt.savefig(img_output, dpi=300, bbox_inches='tight')  # Salva como PNG
    
    # Criar os gráficos de pizza
    pie_output = []

    for resp in grouped.index:
        plt.figure(figsize=(6, 6))

        # Pegar os dados de status para o responsável
        status_counts = grouped.loc[resp]
        labels = status_counts.index
        values = status_counts.values

        # Definir cores de acordo com o status
        pie_colors = []
        for label in labels:
            if label == 'AGD':
                pie_colors.append('gray')
            elif label == 'PRI':
                pie_colors.append('#0072f0')
            elif label == 'OBI':
                pie_colors.append('#ff7043')
            elif label == 'OSP':
                pie_colors.append('#f48fb1')
            else:
                pie_colors.append('lightblue')

        # Função para exibir os valores absolutos nas fatias, omitindo zeros
        def absolute_value(val):
            absolute = int(val / 100. * sum(values))  # Calcula o valor absoluto
            return f'{absolute}' if absolute > 0 else ''  # Retorna valor ou vazio se for 0

        # Criar o gráfico de pizza sem rótulos de cor, com valores em negrito
        plt.pie(values, labels=None, colors=pie_colors, autopct=absolute_value, startangle=90, 
                textprops={'fontsize': 36, 'fontweight': 'bold'})  # Define negrito nos valores

        # Adicionar título centralizado abaixo da pizza
        plt.text(0, -1.2, f'{resp}', ha='center', va='center', fontsize=36, fontweight='bold', fontname='Arial')

        #plt.title(f'Gráfico de Pizza - {resp}', fontsize=18, fontweight='bold')

        # Salvar o gráfico de pizza como imagem
        pie_name = f'outputs/mapas/pizzas/{filename}_{resp}_pizza_prj.png'
        plt.savefig(pie_name, dpi=300, bbox_inches='tight')
        pie_output.append(pie_name)
        plt.close()  # Fecha o gráfico de pizza

    return img_output, pie_output

#### GRÁFICO DE BARRAS DE OBRAS POR ELOS ####
def criar_barra_resp_obr(df, filename, title):
    # Substituir os valores que não estão na lista por 'OUTROS'
    lista_inclusao = ['CEPE','SR-BE', 'SR-BR','SR-CO','SR-MN','SR-NT','SR-RJ','SR-SJ','GAC-AN','COMARA','GECAMP','CO-FZ']
    df['RESP_Fisc_Abr'] = df['RESP_Fisc_Abr'].where(df['RESP_Fisc_Abr'].isin(lista_inclusao), 'OUTROS')
    
    # Agrupar os dados pela coluna 'STATUS' e contar as ocorrências
    grouped = df.groupby(['RESP_Fisc_Abr','STATUS']).size().unstack(fill_value=0)
    
    # Calcular o total de observações para cada valor de 'RESP_PRJ_Abr'
    total_por_resp = grouped.sum(axis=1)

    # Reordenar o DataFrame agrupado com base no total de observações, em ordem decrescente
    grouped = grouped.loc[total_por_resp.sort_values(ascending=False).index]

    # Garantir que 'OUTROS' esteja na última posição
    if 'OUTROS' in grouped.index:
        outros = grouped.loc[['OUTROS']]
        grouped = grouped.drop('OUTROS')
        grouped = pd.concat([grouped, outros])

    # Configurar a fonte para Arial
    plt.rcParams['font.family'] = 'Arial'

    # Criar o gráfico de barras
    plt.figure(figsize=(10, 6))

    # Definir cores para as barras com base no status
    colors = []
    for status in grouped.columns:
        if status == 'AGD':
            colors.append('gray')  # AGD em cinza
        elif status == 'PRI':
            colors.append('#0072f0')  # PRI em azul
        elif status == 'OBI':
            colors.append('#ff7043')  # OBI em laranja
        elif status == 'OSP':
            colors.append('#f48fb1')  # OBI em rosa
        else:
            colors.append('lightblue')  # Cor padrão para outros status

    # Iniciar a variável de base para empilhamento
    bottom_values = np.zeros(len(grouped))
                             
    # Loop para empilhar as barras de acordo com cada status
    for i, status in enumerate(grouped.columns):
        plt.bar(grouped.index, grouped[status], bottom=bottom_values, label=status, color=colors[i], zorder = 3)
        bottom_values += grouped[status]

    # Remover os eixos e bordas
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)

    # Remover as linhas que unem os rótulos do eixo x às barras
    plt.gca().xaxis.tick_bottom()
    plt.gca().tick_params(axis='x', length=0)
    plt.gca().yaxis.tick_left()
    plt.gca().tick_params(axis='y', length=0)

    # Definir os rótulos do eixo x na horizontal
    plt.xticks(rotation=0, fontsize=12, fontweight='bold')

    # Definir os rótulos do eixo y como inteiros
    # Calcular o valor máximo do eixo Y como o múltiplo de 5 imediatamente superior
    max_value = grouped.sum(axis=1).max()
    max_y = np.ceil(max_value / 5) * 5  # Múltiplo de 5 superior
    plt.yticks(range(0, int(max_y) + 1, 5), fontsize=12)

    # Adicionar linhas de grade horizontais
    plt.grid(axis='y', color='darkgray', linestyle='--', linewidth=0.7, zorder=0)

    # Adicionar a legenda personalizada e posicioná-la abaixo do gráfico
    plt.legend(loc='upper center', fontsize=10, frameon=False, borderpad=1, bbox_to_anchor=(0.5, -0.1), ncol = 2)

    # Adicionar uma linha fina preta como eixo x
    plt.axhline(y=0, color='black', linewidth=2)

    plt.title(title, fontsize=18, fontweight='bold')

    # Ajustar o layout para deixar espaço para a legenda abaixo
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)  # Aumenta o espaçamento inferior

    img_output = f'outputs/mapas/{filename}.png'

    # Salvar o gráfico como imagem
    plt.savefig(img_output, dpi=300, bbox_inches='tight')  # Salva como PNG
    
    # Criar os gráficos de pizza
    pie_output = []

    for resp in grouped.index:
        plt.figure(figsize=(6, 6))

        # Pegar os dados de status para o responsável
        status_counts = grouped.loc[resp]
        labels = status_counts.index
        values = status_counts.values

        # Definir cores de acordo com o status
        pie_colors = []
        for label in labels:
            if label == 'AGD':
                pie_colors.append('gray')
            elif label == 'PRI':
                pie_colors.append('#0072f0')
            elif label == 'OBI':
                pie_colors.append('#ff7043')
            elif label == 'OSP':
                pie_colors.append('#f48fb1')
            else:
                pie_colors.append('lightblue')

        # Função para exibir os valores absolutos nas fatias, omitindo zeros
        def absolute_value(val):
            absolute = int(val / 100. * sum(values))  # Calcula o valor absoluto
            return f'{absolute}' if absolute > 0 else ''  # Retorna valor ou vazio se for 0

        # Criar o gráfico de pizza sem rótulos de cor, com valores em negrito
        plt.pie(values, labels=None, colors=pie_colors, autopct=absolute_value, startangle=90, 
                textprops={'fontsize': 36, 'fontweight': 'bold'})  # Define negrito nos valores

        # Adicionar título centralizado abaixo da pizza
        plt.text(0, -1.2, f'{resp}', ha='center', va='center', fontsize=36, fontweight='bold', fontname='Arial')

        #plt.title(f'Gráfico de Pizza - {resp}', fontsize=18, fontweight='bold')

        # Salvar o gráfico de pizza como imagem
        pie_name = f'outputs/mapas/pizzas/{filename}_{resp}_pizza_obr.png'
        plt.savefig(pie_name, dpi=300, bbox_inches='tight')
        pie_output.append(pie_name)
        plt.close()  # Fecha o gráfico de pizza

    return img_output, pie_output

#### GRÁFICO DE BARRAS DE PROSPECÇÃO DE OBRAS POR ELOS ####
def criar_barra_resp_prospec(df, filename, title):
    # Substituir os valores que não estão na lista por 'OUTROS'
    lista_inclusao = ['CEPE','SR-BE', 'SR-BR','SR-CO','SR-MN','SR-NT','SR-RJ','SR-SJ','GAC-AN','COMARA','GECAMP']
    df['RESP_Fisc_Abr'] = df['RESP_Fisc_Abr'].where(df['RESP_Fisc_Abr'].isin(lista_inclusao), 'OUTROS')
    
    # Agrupar os dados pela coluna 'STATUS' e contar as ocorrências
    grouped = df.groupby(['RESP_Fisc_Abr','STATUS_amplo']).size().unstack(fill_value=0)
    
    # Calcular o total de observações para cada valor de 'RESP_PRJ_Abr'
    total_por_resp = grouped.sum(axis=1)

    # Reordenar o DataFrame agrupado com base no total de observações, em ordem decrescente
    grouped = grouped.loc[total_por_resp.sort_values(ascending=False).index]

    # Garantir que 'OUTROS' esteja na última posição
    if 'OUTROS' in grouped.index:
        outros = grouped.loc[['OUTROS']]
        grouped = grouped.drop('OUTROS')
        grouped = pd.concat([grouped, outros])

    # Configurar a fonte para Arial
    plt.rcParams['font.family'] = 'Arial'

    # Criar o gráfico de barras
    plt.figure(figsize=(10, 6))

    # Definir cores para as barras com base no status
    colors = []
    for status in grouped.columns:
        if status == 'Fase de projeto (AGD, PRI, etc.)':
            colors.append('#00b6cb')  
        elif status == 'LIA':
            colors.append('#d79544')  
        elif status == 'OBI':
            colors.append('#ff7043')  
        elif status == 'OSP':
            colors.append('#f48fb1')  
        else:
            colors.append('lightblue')  # Cor padrão para outros status

    # Iniciar a variável de base para empilhamento
    bottom_values = np.zeros(len(grouped))
                             
    # Loop para empilhar as barras de acordo com cada status
    for i, status in enumerate(grouped.columns):
        plt.bar(grouped.index, grouped[status], bottom=bottom_values, label=status, color=colors[i], zorder = 3)
        bottom_values += grouped[status]

    # Remover os eixos e bordas
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)

    # Remover as linhas que unem os rótulos do eixo x às barras
    plt.gca().xaxis.tick_bottom()
    plt.gca().tick_params(axis='x', length=0)
    plt.gca().yaxis.tick_left()
    plt.gca().tick_params(axis='y', length=0)

    # Definir os rótulos do eixo x na horizontal
    plt.xticks(rotation=0, fontsize=12, fontweight='bold')

    # Definir os rótulos do eixo y como inteiros
    # Calcular o valor máximo do eixo Y como o múltiplo de 5 imediatamente superior
    max_value = grouped.sum(axis=1).max()
    max_y = np.ceil(max_value / 5) * 5  # Múltiplo de 5 superior
    plt.yticks(range(0, int(max_y) + 1, 5), fontsize=12)

    # Adicionar linhas de grade horizontais
    plt.grid(axis='y', color='darkgray', linestyle='--', linewidth=0.7, zorder=0)

    # Adicionar a legenda personalizada e posicioná-la abaixo do gráfico
    plt.legend(loc='upper center', fontsize=10, frameon=False, borderpad=1, bbox_to_anchor=(0.5, -0.1), ncol = 2)

    # Adicionar uma linha fina preta como eixo x
    plt.axhline(y=0, color='black', linewidth=2)

    plt.title(title, fontsize=18, fontweight='bold')

    # Ajustar o layout para deixar espaço para a legenda abaixo
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)  # Aumenta o espaçamento inferior

    img_output = f'outputs/mapas/{filename}.png'

    # Salvar o gráfico como imagem
    plt.savefig(img_output, dpi=300, bbox_inches='tight')  # Salva como PNG
    
    # Criar os gráficos de pizza
    pie_output = []

    for resp in grouped.index:
        plt.figure(figsize=(6, 6))

        # Pegar os dados de status para o responsável
        status_counts = grouped.loc[resp]
        labels = status_counts.index
        values = status_counts.values

        # Definir cores de acordo com o status
        pie_colors = []
        for label in labels:
            if label == 'Fase de projeto (AGD, PRI, etc.)':
                pie_colors.append('#00b6cb')
            elif label == 'LIA':
                pie_colors.append('#d79544')
            elif label == 'OBI':
                pie_colors.append('#ff7043')
            elif label == 'OSP':
                pie_colors.append('#f48fb1')
            else:
                pie_colors.append('lightblue')

        # Função para exibir os valores absolutos nas fatias, omitindo zeros
        def absolute_value(val):
            absolute = int(val / 100. * sum(values))  # Calcula o valor absoluto
            return f'{absolute}' if absolute > 0 else ''  # Retorna valor ou vazio se for 0

        # Criar o gráfico de pizza sem rótulos de cor, com valores em negrito
        plt.pie(values, labels=None, colors=pie_colors, autopct=absolute_value, startangle=90, 
                textprops={'fontsize': 36, 'fontweight': 'bold'})  # Define negrito nos valores

        # Adicionar título centralizado abaixo da pizza
        plt.text(0, -1.2, f'{resp}', ha='center', va='center', fontsize=36, fontweight='bold', fontname='Arial')

        #plt.title(f'Gráfico de Pizza - {resp}', fontsize=18, fontweight='bold')

        # Salvar o gráfico de pizza como imagem
        pie_name = f'outputs/mapas/pizzas/{filename}_{resp}_pizza_prospec.png'
        plt.savefig(pie_name, dpi=300, bbox_inches='tight')
        pie_output.append(pie_name)
        plt.close()  # Fecha o gráfico de pizza

    return img_output, pie_output

#### TABELA DE JUSTIFICATIVAS ####
def criar_justificativas(df, year, filename):
    
    summary_df = df[['ID-PW','OM','DESCRIÇÃO','CN','ETPE','TAP ass','TEP ass','VALOR','RECURSO','RESPONSAVEL PROJETO','PRAZO PROJETO VIGENTE + PTA','Justificativa','%PRJ']]

    # Formatar a coluna 'Total Valor (R$)' no formato brasileiro
    summary_df['VALOR'] = pd.to_numeric(summary_df['VALOR'], errors='coerce').fillna(0)
    summary_df['VALOR'] = summary_df['VALOR'].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    # Ordenar o DataFrame pelo campo 'ID-PW'
    summary_df = summary_df.sort_values(by='ID-PW')

    # Renomear as colunas
    summary_df.rename(columns={'ID-PW': 'ID', 'DESCRIÇÃO': 'Descrição', 'TAP ass':'TAP', 'TEP ass': 'TEP', 'VALOR':'Valor Vigente', 'RECURSO': 'Recurso', 'RESPONSAVEL PROJETO': 'Resp. proj.','PRAZO PROJETO VIGENTE + PTA': 'Prazo proj.'}, inplace=True)

    # Tratar a coluna CN para garantir que os valores sejam inteiros
    summary_df['CN'] = pd.to_numeric(summary_df['CN'], errors='coerce').fillna(0).astype(int)  # Converte para numérico, substitui NaN por 0
    summary_df['ETPE'] = pd.to_numeric(summary_df['ETPE'], errors='coerce').fillna(0).astype(int)  # Converte para numérico, substitui NaN por 0
    summary_df['TAP'] = pd.to_numeric(summary_df['TAP'], errors='coerce').fillna(0).astype(int)  # Converte para numérico, substitui NaN por 0
    summary_df['TEP'] = pd.to_numeric(summary_df['TEP'], errors='coerce').fillna(0).astype(int)  # Converte para numérico, substitui NaN por 0
    summary_df['%PRJ'] = pd.to_numeric(summary_df['%PRJ'], errors='coerce').fillna(0)

    # Formatar a coluna 'Prazo proj.' no formato 'YYYY-MM-DD'
    summary_df['Prazo proj.'] = pd.to_datetime(summary_df['Prazo proj.']).dt.strftime('%Y-%m-%d')

    # Geração do HTML com estilos
    
    # Definindo estilo CSS para bordas, alinhamento e cores
    style = """
    <style>
        body {
            font-family: Segou UI Emoji, sans-serif;
            font-size: 14px;
        }

        .main-table {
            border-collapse: collapse;
            width: 1500px;
            font-family: Segou UI Emoji, sans-serif;
            font-size: 14px;
            text-align: center;
        }

        .main-table th {
            padding: 8px;
            background-color: #1565c0; /* Cor de fundo azul */
            color: white; /* Cor da fonte */
            font-weight: bold; /* Fonte em negrito */
        }

        .main-table td {
            padding: 8px;
            border: none;  /* Remove as bordas das células */
        }

        .main-table tr {
            border-bottom: 1px solid black;  /* Adiciona borda preta entre as linhas */
        }

        .main-table td:first-child {
            /*border-left: 1px solid #1976d2;*/
            width: 100px;
        }

        .main-table td:nth-child(3) {
            width: 400px; /* Ajuste a largura da coluna Descrição */
            text-align: left;
        }

        .main-table td:nth-child(8) {
            width: 150px; /* Ajuste a largura da coluna Descrição */
        }

        .main-table td:nth-child(10) {
            width: 150px; /* Ajuste a largura da coluna Descrição */
        }

        .main-table td:nth-child(12) {
            width: 400px; /* Ajuste a largura da coluna Descrição */
            text-align: left;
        }

        .main-table td:last-child {
            /*border-right: 1px solid #1976d2;*/
            text-align: right;
            width: 60px;
        }

        .main-table tr:nth-child(even) {
            background-color: #bbdefb;
        }

        .main-table tr:nth-child(odd) {
            background-color: white;
        }

        .cn-blue {
            background-color: #64b5f6;
            color: #64b5f6;
        }

        .cn-red {
            background-color: #e57373;
            color: #e57373;
        }

        /* Estilo para as barras de progresso */
        .progress-bar {
            position: relative;
            background-color: #f3f3f3;
            border-radius: 5px;
            width: 100%;
            height: 20px;
            margin: 5px 0;
        }

        .progress-bar-fill {
            background-color: #64b5f6;
            height: 100%;
            border-radius: 5px;
            text-align: right;
            padding-right: 5px;
            color: black;
            font-weight: bold;
        }

    </style>
    """

    # Construindo a tabela HTML manualmente
    html_table = '<table class="main-table"><thead><tr>'
    html_table += ''.join(f'<th>{col}</th>' for col in summary_df.columns)  # Cabeçalho
    html_table += '</tr></thead><tbody>'

    for index, row in summary_df.iterrows():
        html_table += '<tr>'
        for col in summary_df.columns:
            # Aplicando classes CSS apenas para a coluna CN
            if col in ['CN', 'ETPE', 'TAP', 'TEP']:
                if row[col] == 1:
                    html_table += f'<td class="cn-blue">{row[col]}</td>'
                elif row[col] == 0:
                    html_table += f'<td class="cn-red">{row[col]}</td>'
                else:
                    html_table += f'<td>{row[col]}</td>'
            # Aplicar a barra de progresso para a coluna de andamento (%)
            elif col == '%PRJ':
                percent = row[col]
                html_table += f'''
                <td>
                    <div class="progress-bar">
                        <div class="progress-bar-fill" style="width: {percent}%;">{percent}%</div>
                    </div>
                </td>'''
            else:
                html_table += f'<td>{row[col]}</td>'  # Para as outras colunas, sem estilização
        html_table += '</tr>'
    
    html_table += '</tbody></table>'

    # Combinando o estilo e a tabela HTML
    html_output = f"{style}\n{html_table}"

    # Salvando a tabela como arquivo HTML
    html_path = 'tabela_resumo_formatado.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    # Configurações para gerar a imagem
    img_options = {
        'format': 'png',
        'encoding': 'UTF-8',
        'width': 500 
    }

    # Converter o HTML em imagem (PNG)
    img_output = f'outputs/{year}/justificativas/{filename}.png'
    imgkit.from_file(html_path, img_output, options=img_options)

    # Excluir o arquivo HTML após gerar a imagem
    if os.path.exists(html_path):
        os.remove(html_path)
        print(f"Arquivo HTML '{html_path}' excluído com sucesso.")

    # Abrir a imagem e obter suas dimensões
    with Image.open(img_output) as img:
        width, height = img.size
        print(f"Dimensões da imagem: {width}x{height} pixels")

    return img_output

#### TABELA DE PROJETOS ENTREGUES POR ELOS ####
def criar_lista_entregues(df, img_output):

    # Definir a data de corte (data de hoje - 30 dias)
    data_limite = datetime.now() - timedelta(days=30)

    # Converter a coluna para datetime, ignorando erros
    df['DATA de assinatura do TEP pelo cliente'] = pd.to_datetime(df['DATA de assinatura do TEP pelo cliente'], errors='coerce', dayfirst=True)

    # Adicionar uma coluna indicando se a linha deve ser destacada
    df['destacar'] = df['DATA de assinatura do TEP pelo cliente'].apply(lambda x: 'destacar' if pd.notna(x) and x > data_limite else '')

    # Seleção das colunas a serem exibidas
    summary_df = df[['ID-PW', 'DESCRIÇÃO', 'OM', 'destacar']]

    # Geração do HTML com estilos
    style = """
    <style>
        body {
            font-family: Segou UI Emoji, sans-serif;
            font-size: 14px;
        }

        .main-table {
            border-collapse: collapse;
            width: 600px;
            font-family: Segou UI Emoji, sans-serif;
            font-size: 14px;
            text-align: center;
        }

        .main-table th {
            padding: 8px;
            background-color: white;
            color: black;
            font-weight: bold;
            text-align: left;
        }

        .main-table td {
            padding: 8px;
            border: none;
        }

        .main-table tr {
            border-bottom: 1px solid black;
        }

        .main-table td:first-child {
            width: 100px;
        }

        .main-table td:nth-child(2) {
            width: 400px;
            text-align: left;
        }

        .main-table td:last-child {
            text-align: left;
            width: 100px;
        }

        /* Estilo para destacar linhas */
        .destacar {
            background-color: #224b89;
            color: white;
            font-weight: bold;
        }

    </style>
    """

    # Gerando o corpo da tabela manualmente com destaque para as linhas
    html_table = f"<table class='main-table'><thead><tr><th>ID-PW</th><th>DESCRIÇÃO</th><th>OM</th></tr></thead><tbody>"
    
    for _, row in summary_df.iterrows():
        class_name = row['destacar']  # Verifica se a linha deve ser destacada
        html_table += f"<tr class='{class_name}'><td>{row['ID-PW']}</td><td>{row['DESCRIÇÃO']}</td><td>{row['OM']}</td></tr>"
    
    html_table += "</tbody></table>"

    # Combinando o estilo e a tabela HTML
    html_output = f"{style}\n{html_table}"

    # Salvando a tabela como arquivo HTML
    html_path = 'lista_entregues.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    # Configurações para gerar a imagem
    img_options = {
        'format': 'png',
        'encoding': 'UTF-8',
        'width': 500 
    }

    # Converter o HTML em imagem (PNG)
    #img_output = f'outputs/{filename}.png'
    imgkit.from_file(html_path, img_output, options=img_options)

    # Excluir o arquivo HTML após gerar a imagem
    if os.path.exists(html_path):
        os.remove(html_path)
        print(f"Arquivo HTML '{html_path}' excluído com sucesso.")

    return img_output

def create_map(images, filename):
    # Abrir a imagem do mapa
    map_image = Image.open('mapa_branco.png').convert("RGBA")

    pizza_images= []

    for image in images:
        if 'CEPE' in image:
            pizza_images.append((image,(525,540)))
        elif 'SR-MN' in image:
            pizza_images.append((image,(70,70)))
        elif 'COMARA' in image:
            pizza_images.append((image,(250,110)))
        elif 'SR-BE' in image:
            pizza_images.append((image,(410,50)))
        elif 'SR-NT' in image:
            pizza_images.append((image,(550,170)))
        elif 'SR-BR' in image:
            pizza_images.append((image,(390,260)))
        elif 'SR-RJ' in image:
            pizza_images.append((image,(500,380)))
        elif 'SR-SJ' in image:
            pizza_images.append((image,(325,400)))
        elif 'SR-CO' in image:
            pizza_images.append((image,(335,540)))
        elif 'GECAMP' in image:
            pizza_images.append((image,(70,350)))
        elif 'GAC-AN' in image:
            pizza_images.append((image,(255,260)))
        else:
            pizza_images.append((image,(70,540)))

    # Tamanho desejado para os gráficos de pizza (largura, altura)
    new_size = (135, 135)  # Altere para o tamanho desejado

    # Função para remover o fundo branco
    def remove_white_background(image):
        # Convertendo a imagem para RGBA
        image = image.convert("RGBA")
        data = image.getdata()
        
        new_data = []
        for item in data:
            # Alterar pixels brancos (ou quase brancos) para transparentes
            if item[0] > 200 and item[1] > 200 and item[2] > 200:  # Ajuste o limiar conforme necessário
                new_data.append((255, 255, 255, 0))  # Tornar transparente
            else:
                new_data.append(item)
        
        image.putdata(new_data)
        return image

    # Sobrepor cada gráfico de pizza no mapa
    for pizza_path, position in pizza_images:
        pizza_image = Image.open(pizza_path)  # Não precisa converter ainda
        
        # Remover fundo branco
        pizza_image = remove_white_background(pizza_image)

        # Redimensionar a imagem de pizza
        pizza_image = pizza_image.resize(new_size, Image.LANCZOS)  # Usando LANCZOS para qualidade

        # Colar a pizza no mapa, preservando a transparência
        map_image.paste(pizza_image, position, pizza_image)  # Usar a imagem com canal alfa como máscara

    # Salvar a nova imagem resultante
    map_image.save(f'outputs/mapas/{filename}.png', format='PNG')

    return f'outputs/mapas/{filename}.png'