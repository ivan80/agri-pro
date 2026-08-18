"""Calendario colturale: operazioni mensili per gruppo di specie (guida di riferimento)."""

GROUPS = [
    {"key": "pomacee", "label": "Pomacee (Melo, Pero)", "emoji": "🍎"},
    {"key": "drupacee", "label": "Drupacee (Susino, Ciliegio, Albicocco)", "emoji": "🍒"},
    {"key": "pesco", "label": "Pesco", "emoji": "🍑"},
    {"key": "vite", "label": "Vite / Uva", "emoji": "🍇"},
    {"key": "fico", "label": "Fico", "emoji": "🫒"},
    {"key": "nocciolo", "label": "Nocciolo", "emoji": "🌰"},
    {"key": "avocado", "label": "Avocado", "emoji": "🥑"},
]

MONTHS = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
          "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]


def _cal(*rows):
    return {i + 1: rows[i] for i in range(12)}


POMACEE = _cal(
    ["Potatura secca", "Trattamento rame su tagli"],
    ["Fine potatura", "Concimazione di fondo"],
    ["Ticchiolatura: primi preventivi", "Punta verde"],
    ["Ticchiolatura + oidio (fase critica)", "Diradamento gemme"],
    ["Fioritura: NO insetticidi", "Carpocapsa: monitoraggio trappole"],
    ["Carpocapsa 1ª generazione", "Diradamento frutti", "Irrigazione"],
    ["Oidio + acari (estate)", "Irrigazione costante"],
    ["Carpocapsa 2ª generazione", "Irrigazione"],
    ["Pre-raccolta: rispettare carenza", "Raccolta precoci"],
    ["Raccolta", "Concimazione autunnale"],
    ["Rame post-raccolta (cadute foglie)", "Analisi terreno"],
    ["Riposo", "Potatura secca inizio"],
)

DRUPACEE = _cal(
    ["Potatura secca (a fine mese)", "Rame"],
    ["Rigonfiamento gemme", "Corineo: rame"],
    ["Fioritura (drupacee precoci): NO trattamenti", "Monilia: preventivo"],
    ["Allegagione", "Afidi: monitoraggio", "Concimazione"],
    ["Monilia + afidi", "Cidia/Anarsia trappole", "Irrigazione"],
    ["Accrescimento frutti", "Acari estate", "Irrigazione"],
    ["Maturazione precoci", "Monilia pre-raccolta"],
    ["Raccolta", "Cocciniglia"],
    ["Post-raccolta", "Concimazione"],
    ["Pulizia Corineo (rame)", "Cadute foglie"],
    ["Riposo", "Rame"],
    ["Potatura secca", "Riposo"],
)

PESCO = _cal(
    ["Potatura", "Rame"],
    ["Bolla: FINESTRA CRITICA (rame)", "Gemma gonfia"],
    ["Bolla fine finestra", "Fioritura: NO trattamenti"],
    ["Monilia post-fioritura", "Afidi", "Concimazione azotata"],
    ["Cidia + Anarsia", "Irrigazione"],
    ["Accrescimento", "Acari", "Irrigazione costante"],
    ["Monilia pre-raccolta", "Maturazione"],
    ["Raccolta", "Cidia 2ª gen"],
    ["Post-raccolta", "Concimazione"],
    ["Corineo (rame)", "Cadute foglie"],
    ["Riposo", "Rame"],
    ["Potatura", "Riposo"],
)

VITE = _cal(
    ["Potatura secca", "Riposo"],
    ["Pianto della vite", "Fine potatura"],
    ["Gemma gonfia", "Pulizia"],
    ["Germogliamento", "Peronospora: primi controlli"],
    ["Pre-fioritura: zolfo (oidio)", "Peronospora"],
    ["Fioritura + allegagione", "Zolfo post-fioritura"],
    ["Oidio + peronospora", "Cimice asiatica", "Irrigazione"],
    ["Chiusura grappolo", "Botrite prevenzione"],
    ["Invaiatura", "Riduzione trattamenti (carenza)"],
    ["Vendemmia", "Raccolta"],
    ["Post-raccolta (rame)", "Concimazione"],
    ["Riposo", "Potatura"],
)

FICO = _cal(
    ["Riposo", "Potatura"],
    ["Rigonfiamento gemme", "Cocciniglia svernante"],
    ["Comparsa foglie", "Cocciniglia: olio bianco"],
    ["Sviluppo vegetativo", "Tripidi"],
    ["Accrescimento", "Ragnetto rosso", "Irrigazione"],
    ["Fioritura interna", "Irrigazione"],
    ["Pre-invaiatura", "Ragnetto (caldo secco)"],
    ["Raccolta (fioroni/forniti)", "Bentonite"],
    ["Raccolta", "Riduzione irrigazione"],
    ["Post-raccolta", "Concimazione"],
    ["Cadute foglie", "Pulizia"],
    ["Riposo", "Potatura"],
)

NOCCIOLO = _cal(
    ["Riposo", "Potatura"],
    ["Fioritura amenti: NO trattamenti", "Impollinazione"],
    ["Comparsa foglie", "Afidi + oidio"],
    ["Sviluppo vegetativo", "Oidio"],
    ["Allegagione", "Cimice asiatica inizio", "Concimazione"],
    ["Accrescimento", "Cimice asiatica (critico)", "Irrigazione"],
    ["Invaiatura", "Cimice + oidio"],
    ["Maturazione", "Raccolta inizio"],
    ["Raccolta", "Cimici"],
    ["Post-raccolta (gleosporiosi)", "Concimazione autunnale"],
    ["Cadute foglie", "Pulizia"],
    ["Riposo", "Potatura"],
)

AVOCADO = _cal(
    ["PROTEGGERE dal gelo", "Riparo/telo"],
    ["Protezione freddo", "Riposo"],
    ["Ripresa vegetativa", "Concimazione"],
    ["Crescita primaverile", "Cocciniglia monitoraggio"],
    ["Fioritura", "Irrigazione"],
    ["Allegagione", "Irrigazione costante"],
    ["Estate: ragnetto rosso", "Irrigazione abbondante"],
    ["Accrescimento frutti", "Ombreggiamento se necessario"],
    ["Autunno: riduzione acqua", "Concimazione leggera"],
    ["Preparazione al freddo", "Pacciamatura"],
    ["Protezione gelo", "Riparo"],
    ["PROTEGGERE dal gelo", "Riposo"],
)

CALENDARS = {"pomacee": POMACEE, "drupacee": DRUPACEE, "pesco": PESCO, "vite": VITE,
             "fico": FICO, "nocciolo": NOCCIOLO, "avocado": AVOCADO}


def calendar_for(group):
    cal = CALENDARS.get(group, POMACEE)
    return [{"month": i, "name": MONTHS[i - 1], "operations": cal.get(i, [])} for i in range(1, 13)]
