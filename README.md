# 📊 AutoBQS - Project Analysis

This project automates the analysis and generation of graphs and tables for monitoring enginnering projects. It processes data, generates summaries, and creates visualizations that help track project progress.

## 🚀 Features

✅ Creation of output **directories**
✅ Data collection from **Google Sheets** via API
✅ Data processing and transformation
✅ Generation of **charts and tables** for project tracking
✅ Support for different project statuses (AGD, PRI, PRC, OBI, etc.)
✅ Exporting summaries as **images** 

## 📂 Project Structure

```
📦 autoBQS
├── 📜 bqs.py # Main script
├── 📜 helpers.py # Auxiliary functions
├── 📜 get_data_pw.py # Data collection from PlanInfraWeb
├── 📂 outputs # Generated images
|    ├── 2023
|    |  ├── entregues
|    |  ├── justificativas
|    |  ├── resumos
|    |  ├── status
|    |  ├── status_det
|    ├── 2024
|    |  ├── entregues
|    |  ├── justificativas
|    |  ├── resumos
|    |  ├── status
|    |  ├── status_det
|    ├── 2025
|    |  ├── entregues
|    |  ├── justificativas
|    |  ├── resumos
|    |  ├── status
|    |  ├── status_det
|    ├── mapas
|    |        ├── pizzas
└── 📜 README.md # Documentation
```

## 🛠️ Installation

1️⃣ **Clone this repository**  
```sh
git clone https://github.com/seu-usuario/autoBQS.git
cd autoBQS
```
2️⃣ Create a virtual environment (optional but recommended)
```sh
python -m venv venv
source venv/bin/activate  # No Linux/macOS
venv\Scripts\activate     # No Windows
```
3️⃣ Install dependencies
```sh
pip install -r requirements.txt
```
4️⃣ Create a `.env` file with your credentials:
```sh
GSHEET_CRED="caminho/para/suas/credenciais.json"
GSHEET_KEY_SHEET="URL_da_sua_planilha"
USUARIO_PROXY="seu_usuario"
PASS_PROXY="sua_senha"
ENDERECO_PROXY="proxy.exemplo.com:8080"
```
▶️ How to Run
```sh
python bqs.py
```
The generated graphs will be in the `outputs/` folder.

📦 Dependencies
The script uses the following libraries:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.parse
import os
import warnings
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime, timedelta
```
