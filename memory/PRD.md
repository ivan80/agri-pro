# PRD — Pomario (Gestione Frutteto Misto)

## Problem Statement (original, IT)
Sito web che spiega/sponsorizza e permette di scaricare un'app per la gestione delle piante da frutto (prodotti, irrigazione, fasi fenologiche) di un frutteto misto. Deve permettere di collegare una stazione meteo Ecowitt completa di sensori. User-friendly per appassionati. Periodo di prova + abbonamento annuale o acquisto a vita.

## User Choices
- Sito vetrina + app demo con login/auth + abbonamenti
- Pagamenti: NO reali (solo mostra piani) — MOCK pricing
- Ecowitt: demo reale (API Cloud v3 con fallback dati demo)
- AI per consigli sulle piante (Claude via Emergent LLM key)
- Stile: sfondo chiaro, verdi/azzurri/arancioni. Auth: JWT email+password

## Architecture
- Backend: FastAPI + MongoDB (motor). JWT httpOnly cookie auth (bcrypt). Routes under /api.
- Frontend: React 19 + Tailwind + framer-motion + lenis + recharts. Fonts: Cabinet Grotesk / Cormorant Garamond / Satoshi.
- Integrations: emergentintegrations (Claude sonnet-4-6) for AI advisor; Ecowitt Cloud API /device/real_time.

## Implemented (2026-07-17)
- Auth: register (14gg trial), login, logout, me. Admin seed (admin@frutteto.it).
- Piante: CRUD con isolamento per utente.
- Irrigazione: create/list. Stats dashboard.
- Fasi fenologiche: 6 fasi di riferimento.
- Meteo Ecowitt: /api/weather (reale se chiavi configurate, altrimenti DEMO) + settings per-utente + grafici 24h.
- Assistente AI: consigli colturali in italiano.
- Piani: trial / annuale 39€ / lifetime 129€ (no pagamento).
- Landing award-worthy: hero cinetico mask-reveal, marquee, capitoli manifesto, sezione Ecowitt, pricing bento, download CTA. Dashboard con sidebar.
- Tested: backend 17/17 pytest, frontend tutti i flussi critici OK.

## MAJOR REWORK (2026-07-17) — Motore Agronomico (da 4 PDF utente "Frutteto-Agro")
Adottata la logica dell'app dell'utente. App ora è un motore agronomico multi-utente (auth JWT), avviato VERGINE (nessuna pianta/prodotto pre-inseriti).
- Backend nuovo (server.py + engine.py + phases.py):
  - Piante con fasi fenologiche BBCH auto-generate da template per specie (drupacee, pesco, biricoccolo, pomacee, vite, fico, nocciolo, avocado). Ogni fase ha rischio fungino/insetti/acari 0-3.
  - Prodotti fitosanitari (categoria, persistenza, carenza, soglia dilavamento, dose, in_stock) + compatibilità prodotto-pianta-fase.
  - Trattamenti (calcolo scadenza da persistenza, stato valid/leached/expired/superseded, supersede stessa categoria).
  - Motore (POST /cycle/run): assess_fungal_risk, is_raining, estimate_leaf_wetness, check_leaching (dilavamento post-pioggia), check_expiry, blocco pioggia, generate_phase_recommendations, alert rischio fungino critico.
  - Raccomandazioni (execute→trattamento, dismiss), Alert (ack), Meteo Ecowitt (reale+demo, storico), irrigazione (soglie suolo), config soglie.
  - AI: generate-phases (Claude), advisor (Claude).
- Frontend nuovo: Dashboard (KPI, Ecowitt, irrigazione, run ciclo), Piante & Fasi (add + dettaglio fasi + set fase + AI), Prodotti, Trattamenti, Raccomandazioni, Alert, Meteo, Assistente AI, Impostazioni. Nav a gruppi.
- Test: backend 27/27 pytest, tutti i flussi frontend 100%.

## UPDATE (2026-08-18) — 4 richieste utente
- Precedenza prodotti registrati: il motore auto-abbina i prodotti in magazzino per categoria di rischio (rame/fungicida/zolfo→fungino, insetticida→insetti, acaricida→acari) anche senza compatibilità manuale.
- Meteo da posizione: se non c'è stazione Ecowitt, scarica il meteo via Open-Meteo (lat/lon in Impostazioni, geolocalizzazione browser). Fallback a demo se irraggiungibile. Sorgenti: ecowitt → open-meteo → demo.
- Dosi per litro: prodotti usano dose_per_l (g/L); prompt AI aggiornati a dosi per litro.
- Promemoria concimazione: sezione Concimazioni (stallatico, letame, azotato…) con data promemoria; il ciclo motore genera alert quando scaduto.
- Test: backend 36/36 pytest, frontend 100%. Logout ora torna alla landing.

## UPDATE (2026-08-18b) — Miglioramenti approvati dall'utente
- Diagnosi Foto AI: POST /api/diagnosis (Claude vision via emergentintegrations ImageContent), upload foto con resize client-side, referto in italiano (diagnosi, gravità, sintomi, trattamento con dosi/L, prevenzione) + storico.
- Piano di Lavoro: GET /api/workplan raggruppa le raccomandazioni attive per prodotto in interventi con litri acqua (n_piante × L/pianta) e quantità prodotto (dose/L × litri) + avvisi incompatibilità (rame+zolfo).
- Modifica Concimazioni: PUT /api/fertilization/{id} + UI edit.
- Test: backend 42/42 pytest, frontend 100%. Vision AI verificata.

## UPDATE (2026-08-18c) — Telegram + Calendario + Report + Ciclo automatico
- Telegram: bot a livello app (TELEGRAM_BOT_TOKEN in .env, ancora VUOTO su richiesta utente → invio disattivo finché non lo aggiunge). Ogni utente inserisce la propria telegram_chat_id in Impostazioni (box istruzioni 3 passi). POST /api/telegram/test, notify_cycle invia riepilogo dopo il ciclo. Gestione errori pulita (400, mai 500) senza token.
- Calendario Colturale: calendar_data.py (7 gruppi specie × 12 mesi di operazioni), GET /api/calendar/groups e /api/calendar/{group}. UI con tab specie e mese corrente evidenziato.
- Report: GET /api/report (aggregati piante/trattamenti/concimazioni/diagnosi), pagina stampabile (window.print → PDF) con CSS @media print.
- Ciclo automatico: config auto_cycle_enabled + loop asyncio orario in startup (_auto_cycle_loop) che esegue il motore e invia notifiche Telegram per gli utenti con auto attivo. Toggle in Impostazioni.
- Test: backend 53/53 pytest, frontend 100%.

## DEFERRED dai PDF (non ancora implementati)
- Piano di Lavoro (ottimizzatore miscele/vasca litri), Diagnosi foto AI, pH & irrigazione (tracking pH per pianta + fertilizzazioni), Calendario colturale (matrice specie×mese), Grafici meteo avanzati, Report PDF/HTML, notifiche Telegram (richiede bot token utente), previsioni 7 giorni Open-Meteo, foto/note per pianta, matrice incompatibilità/sinergie prodotti, scheduler cron automatico.

## Backlog / Next
- P1: Integrazione pagamenti reale (Stripe) per abbonamenti/lifetime.
- P1: Ecowitt — mappatura completa multi-canale sensori suolo + storico persistito su DB.
- P2: Notifiche/promemoria fenologici e calendario trattamenti.
- P2: Gestione "prodotti" (magazzino fitofarmaci/concimi) con registro trattamenti.
- P2: Export PDF quaderno di campagna; multi-frutteto.
- P2: Hardening: try/except su ObjectId invalidi (400 invece di 500).

## Credentials
See /app/memory/test_credentials.md (admin@frutteto.it / Frutteto2026!).
