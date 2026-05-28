from __future__ import annotations

from pathlib import Path

ANO_INICIO = 2016
ANO_FIM = 2026

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
PROCESSED = BASE_DIR / "data" / "processed"

# Sem barra de ferramentas Plotly (zoom, pan, download, etc.)
PLOTLY_CONFIG: dict = {
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False,
}

UF_NOMES = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}
