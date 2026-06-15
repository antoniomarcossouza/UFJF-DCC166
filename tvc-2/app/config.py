from pathlib import Path

# Raiz do projeto (pasta marketing-roi/)
BASE_DIR  = Path(__file__).resolve().parent.parent

# Pasta onde ficam os CSVs gerados pelo notebook 02
PROCESSED = BASE_DIR / "data" / "processed"

# Nomes amigáveis para os IDs de campanha presentes no dataset
CAMPANHA_NOMES = {
    916:  "Campanha A",
    936:  "Campanha B",
    1178: "Campanha C",
}


# desativa toolbar, zoom por scroll e duplo-clique para reset
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "scrollZoom":     False,
    "doubleClick":    False,
}
