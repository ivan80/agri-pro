"""Template fasi fenologiche (scala BBCH) per specie da frutto."""


def _p(code, name, order, desc, rf, ri, ra):
    return {"phase_code": code, "phase_name": name, "phase_order": order,
            "description": desc, "risk_fungal": rf, "risk_insect": ri, "risk_acarid": ra}


DRUPACEE = [
    _p('A', 'Dormienza', 1, 'Gemme a riposo, trattamenti invernali e concimazione', 0, 0, 0),
    _p('B', 'Gemma gonfia', 2, 'Gonfiamento gemme, Corineo e Cancro batterico', 1, 0, 0),
    _p('C', 'Punta verde/Rosa', 3, 'Prima comparsa verde, inizia rischio fungino', 2, 1, 0),
    _p('D', 'Bottone rosa', 4, 'Boccioli separati, preventivo fungino', 2, 1, 0),
    _p('E', 'Fioritura', 5, 'NESSUN TRATTAMENTO: protezione api e impollinazione', 3, 1, 0),
    _p('F', 'Caduta petali', 6, 'Fine fioritura, Monilia fase critica', 3, 2, 0),
    _p('G', 'Allegagione', 7, 'Frutto legato, Monilia + afidi attivi', 3, 2, 1),
    _p('H', 'Accrescimento I', 8, 'Frutto in crescita, insetti e funghi', 2, 2, 1),
    _p('I', 'Accrescimento II', 9, 'Indurimento nocciolo, cocciniglia + acari estate', 2, 2, 2),
    _p('J', 'Pre-invaiatura', 10, 'Frutto vicino a maturazione, Monilia critica', 3, 1, 1),
    _p('K', 'Maturazione/Raccolta', 11, 'Raccolta, rispettare carenza prodotti', 2, 1, 0),
    _p('L', 'Post-raccolta', 12, 'Pulizia funghi + concimazione autunnale', 1, 0, 0),
]

PESCO = [
    _p('A', 'Dormienza', 1, 'Gemme a riposo, azoto fondamentale per pesco', 0, 0, 0),
    _p('B', 'Gemma gonfia', 2, 'CRITICO: finestra Bolla, trattare entro questa fase', 3, 0, 0),
    _p('C', 'Punta rosa', 3, 'Bolla ancora attiva, trattamento rame', 3, 0, 0),
    _p('D', 'Bottone rosa', 4, 'Fine finestra Bolla, preventivo Monilia', 2, 1, 0),
    _p('E', 'Fioritura', 5, 'NESSUN TRATTAMENTO, Monilia in agguato', 3, 1, 0),
    _p('F', 'Caduta petali', 6, 'Monilia critica post-fioritura', 3, 2, 0),
    _p('G', 'Allegagione', 7, 'Cidia larve + afidi, trattare con Neem', 2, 2, 1),
    _p('H', 'Accrescimento I', 8, 'Cidia + Anarsia attivi, barriera fisica', 2, 3, 1),
    _p('I', 'Accrescimento II', 9, 'Cidia + acari, estate calda', 2, 2, 2),
    _p('J', 'Pre-invaiatura', 10, 'Monilia pre-raccolta URGENTE', 3, 2, 1),
    _p('K', 'Maturazione/Raccolta', 11, 'Raccolta, carenza 0', 2, 1, 0),
    _p('L', 'Post-raccolta', 12, 'Pulizia Corineo + concimazione autunnale', 1, 0, 0),
]

BIRICOCCOLO = [
    _p('A', 'Dormienza', 1, 'Gemme a riposo, pulizia invernale', 0, 0, 0),
    _p('B', 'Gemma gonfia', 2, 'Bolla + Corineo, doppio rischio', 3, 0, 0),
    _p('C', 'Punta verde/Rosa', 3, 'Bolla critica + Monilia inizia', 3, 1, 0),
    _p('D', 'Bottone rosa', 4, 'Fine Bolla, Monilia preventivo', 2, 1, 0),
    _p('E', 'Fioritura', 5, 'NESSUN TRATTAMENTO', 3, 1, 0),
    _p('F', 'Caduta petali', 6, 'Monilia + Corineo fase critica', 3, 2, 0),
    _p('G', 'Allegagione', 7, 'Monilia + afidi', 3, 2, 1),
    _p('H', 'Accrescimento I', 8, 'Corineo + acari', 2, 2, 1),
    _p('I', 'Accrescimento II', 9, 'Acari + cocciniglia estate', 2, 2, 2),
    _p('J', 'Pre-invaiatura', 10, 'Monilia pre-raccolta critica', 3, 1, 1),
    _p('K', 'Maturazione/Raccolta', 11, 'Raccolta', 2, 1, 0),
    _p('L', 'Post-raccolta', 12, 'Pulizia + concimazione', 1, 0, 0),
]

POMACEE = [
    _p('A', 'Dormienza', 1, 'Gemme a riposo, cancri rameali invernali', 0, 0, 0),
    _p('B', 'Gemma gonfia', 2, 'Gonfiamento gemme', 1, 0, 0),
    _p('C', 'Punta verde', 3, 'TICCHIOLATURA: trattamento critico', 2, 1, 0),
    _p('D', 'Orecchie di topo', 4, 'Ticchiolatura + oidio attivi', 2, 1, 0),
    _p('E', 'Mezza foglia', 5, 'Ticchiolatura + oidio fase critica', 3, 1, 1),
    _p('F', 'Bottone rosa/bianco', 6, 'Pre-fioritura, ticchiolatura critica', 3, 2, 1),
    _p('G', 'Fioritura', 7, 'NESSUN TRATTAMENTO, ticchiolatura massima', 3, 2, 1),
    _p('H', 'Caduta petali', 8, 'Ticchiolatura + Carpocapsa inizia', 3, 2, 1),
    _p('I', 'Allegagione', 9, 'Ticchiolatura + Carpocapsa (verme mele)', 3, 3, 1),
    _p('J', 'Accrescimento I', 10, 'Carpocapsa critica + oidio', 2, 3, 1),
    _p('K', 'Accrescimento II', 11, 'Estate: oidio + acari + Carpocapsa', 2, 2, 2),
    _p('L', 'Pre-raccolta', 12, 'Rispettare carenza 30gg', 1, 1, 1),
    _p('M', 'Raccolta', 13, 'Raccolta, nessun trattamento', 1, 1, 0),
    _p('N', 'Post-raccolta', 14, 'Ticchiolatura + cancri + concimazione', 1, 0, 0),
]

VITE = [
    _p('A', 'Gemma invernale', 1, 'Riposo vegetativo, pulizia e concimazione', 0, 0, 0),
    _p('B', 'Gemma gonfia', 2, 'Gonfiamento gemma, pulizia invernale', 1, 0, 0),
    _p('C', 'Punte verdi', 3, 'Prime punte verdi, peronospora inizia', 1, 0, 0),
    _p('D', 'Foglie aperte', 4, 'Peronospora + oidio iniziano', 2, 1, 0),
    _p('E', 'Grappolo pulizia', 5, 'Peronospora + oidio attivi', 2, 1, 1),
    _p('F', 'Grappolo allungato', 6, 'Oidio critico, fiori separati', 2, 2, 1),
    _p('G', 'Pre-fioritura', 7, 'TRATTAMENTO CHIAVE: zolfo pre-fioritura', 3, 2, 1),
    _p('H', 'Fioritura', 8, 'Fioritura, no rame né zolfo', 3, 2, 1),
    _p('I', 'Post-fioritura', 9, 'TRATTAMENTO CHIAVE: zolfo post-fioritura', 3, 2, 1),
    _p('J', 'Acini pisello', 10, 'Oidio + cimice asiatica inizia', 2, 2, 1),
    _p('K', 'Chiusura grappolo', 11, 'Botrite + cimice asiatica', 2, 2, 1),
    _p('L', 'Pre-invaiatura', 12, 'Cimice + botrite pre-raccolta', 2, 3, 1),
    _p('M', 'Invaiatura/Raccolta', 13, 'Raccolta, nessun trattamento', 1, 2, 0),
    _p('N', 'Post-raccolta', 14, 'Pulizia peronospora + concimazione', 1, 0, 0),
]

FICO = [
    _p('A', 'Dormienza', 1, 'Riposo vegetativo invernale', 0, 0, 0),
    _p('B', 'Rigonfiamento gemme', 2, 'Inizio attività cocciniglia svernante', 0, 1, 0),
    _p('C', 'Comparsa foglie', 3, 'Cocciniglia neanidi, ideale trattamento', 0, 2, 0),
    _p('D', 'Sviluppo vegetativo', 4, 'Cocciniglia + tripidi attivi', 0, 2, 1),
    _p('E', 'Accrescimento frutti', 5, 'Ragnetto rosso, caldo secco critico', 0, 2, 3),
    _p('F', 'Pre-invaiatura', 6, 'Ragnetto + tripidi vicino a raccolta', 0, 2, 3),
    _p('G', 'Raccolta', 7, 'Solo Bentonite, carenza 0', 0, 1, 1),
    _p('H', 'Post-raccolta', 8, 'Pulizia fine stagione + concimazione', 1, 0, 0),
]

NOCCIOLO = [
    _p('A', 'Dormienza', 1, 'Riposo vegetativo, pulizia invernale', 0, 0, 0),
    _p('B', 'Fioritura amenti', 2, 'NESSUN TRATTAMENTO, impollinazione anemofila', 0, 0, 0),
    _p('C', 'Comparsa foglie', 3, 'Afidi + oidio iniziano (aprile)', 2, 1, 0),
    _p('D', 'Sviluppo vegetativo', 4, 'Oidio + afidi attivi', 2, 2, 0),
    _p('E', 'Allegagione', 5, 'Cimice asiatica inizia + oidio', 2, 2, 1),
    _p('F', 'Accrescimento', 6, 'Cimice asiatica critica (giu-lug)', 2, 3, 1),
    _p('G', 'Invaiatura', 7, 'Cimice + oidio, frutto a rischio', 1, 3, 1),
    _p('H', 'Maturazione/Raccolta', 8, 'Raccolta (ago-set)', 0, 1, 0),
    _p('I', 'Post-raccolta', 9, 'Gleosporiosi + concimazione autunnale', 1, 0, 0),
]

AVOCADO = [
    _p('A', 'Dormienza/Inverno', 1, 'PROTEGGERE sotto 5°C, coprire o riparare', 0, 0, 0),
    _p('B', 'Crescita primaverile', 2, 'Cocciniglia possibile, monitorare', 0, 1, 0),
    _p('C', 'Estate', 3, 'Ragnetto rosso con caldo secco', 0, 1, 2),
    _p('D', 'Autunno', 4, 'Preparazione al freddo, ridurre irrigazione', 0, 0, 0),
]

GENERICO = DRUPACEE

PHASE_TEMPLATES = {
    "drupacee": DRUPACEE, "pesco": PESCO, "biricoccolo": BIRICOCCOLO, "pomacee": POMACEE,
    "vite": VITE, "fico": FICO, "nocciolo": NOCCIOLO, "avocado": AVOCADO, "generico": GENERICO,
}

SPECIES_LIST = [
    {"name": "Melo", "emoji": "🍎", "template": "pomacee"},
    {"name": "Pero", "emoji": "🍐", "template": "pomacee"},
    {"name": "Susino", "emoji": "🫐", "template": "drupacee"},
    {"name": "Ciliegio", "emoji": "🍒", "template": "drupacee"},
    {"name": "Albicocco", "emoji": "🧡", "template": "drupacee"},
    {"name": "Pesco", "emoji": "🍑", "template": "pesco"},
    {"name": "Biricoccolo", "emoji": "🌸", "template": "biricoccolo"},
    {"name": "Vite/Uva", "emoji": "🍇", "template": "vite"},
    {"name": "Fico", "emoji": "🫒", "template": "fico"},
    {"name": "Nocciolo", "emoji": "🌰", "template": "nocciolo"},
    {"name": "Avocado", "emoji": "🥑", "template": "avocado"},
    {"name": "Agrume", "emoji": "🍊", "template": "generico"},
    {"name": "Kaki", "emoji": "🟠", "template": "generico"},
    {"name": "Altro", "emoji": "🌳", "template": "generico"},
]

_SPECIES_MAP = {s["name"].lower(): s["template"] for s in SPECIES_LIST}


def template_for_species(species: str):
    key = (species or "").lower().strip()
    tmpl = _SPECIES_MAP.get(key)
    if not tmpl:
        for word, t in [("pesc", "pesco"), ("melo", "pomacee"), ("pero", "pomacee"),
                        ("vit", "vite"), ("uva", "vite"), ("fico", "fico"),
                        ("nocci", "nocciolo"), ("avocad", "avocado"), ("biric", "biricoccolo"),
                        ("susin", "drupacee"), ("cilieg", "drupacee"), ("albicocc", "drupacee")]:
            if word in key:
                tmpl = t
                break
    return [dict(p) for p in PHASE_TEMPLATES.get(tmpl or "generico", GENERICO)]
