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

## Backlog / Next
- P1: Integrazione pagamenti reale (Stripe) per abbonamenti/lifetime.
- P1: Ecowitt — mappatura completa multi-canale sensori suolo + storico persistito su DB.
- P2: Notifiche/promemoria fenologici e calendario trattamenti.
- P2: Gestione "prodotti" (magazzino fitofarmaci/concimi) con registro trattamenti.
- P2: Export PDF quaderno di campagna; multi-frutteto.
- P2: Hardening: try/except su ObjectId invalidi (400 invece di 500).

## Credentials
See /app/memory/test_credentials.md (admin@frutteto.it / Frutteto2026!).
