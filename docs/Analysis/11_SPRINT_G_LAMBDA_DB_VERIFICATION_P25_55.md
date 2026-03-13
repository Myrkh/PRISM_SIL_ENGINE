# PRISM SIL Engine — Sprint G
## Vérification Integration p25–55 : PDS Data Handbook 2021

**Version:** v0.7.2  
**Date:** 2026-03-13  
**Source primaire:** SINTEF PDS Data Handbook, 2021 Edition, pages 25–55  
**Auteur:** Claude (Anthropic) — démarche vérification scientifique systématique

---

## 1. Périmètre vérifié

Pages 25–55 du handbook couvrant :

| Table / Section | Contenu | Pages |
|---|---|---|
| Table 3.6 | Miscellaneous final elements | 25 |
| Table 3.7 | Subsea input devices | 26 |
| Table 3.8 | Subsea control logic & umbilicals | 27 |
| Table 3.9 | Subsea final elements | 27 |
| Table 3.10 | Downhole well completion valves | 27 |
| Table 3.11 | Drilling equipment | 28 |
| Table 3.12 | Generic β values | 29 |
| §3.5 | Diagnostic Coverage (DC) | 29–32 |
| §3.6 | Proof Test Coverage (PTC) | 33–36 |
| §3.7 + Table 3.14 | Random Hardware Failure Fraction (RHF) | 36–39 |
| §3.8 + Tables 3.15–3.18 | Uncertainty / IC 90% | 40–45 |
| §4.1 | Explication dossiers | 46–48 |
| Dossier §4.2.1 | Position Switch | 49 |
| Dossier §4.2.2 | Aspirator system incl. flow switch | 50 |
| Dossier §4.2.3 | Pressure Transmitter (+ piézorésistif) | 51–52 |
| Dossier §4.2.4 | Level Transmitter (+ 4 sous-types) | 53–54 |
| Dossier §4.2.5 | Temperature Transmitter (+ thermocouple) | 55 |

---

## 2. Méthodologie de vérification

Chaque valeur intégrée dans `lambda_db.py` a été comparée **valeur par valeur** contre le document source après réception du PDF `p25-55__1_.pdf`. Le script de vérification (`python3 -c "..."`) compare :

- `lambda_DU` (moyenne, ×10⁻⁶/h → ×10⁻⁶ converti)
- `lambda_DU_70` (borne 70%)
- `lambda_DU_90_lo` / `lambda_DU_90_hi` (IC 90%)
- `DC` (couverture diagnostique)
- `beta` (facteur de cause commune)
- `RHF` (Random Hardware Failure Fraction)
- Présence/absence d'entrées

---

## 3. Résultats de vérification

### 3.1 Valeurs conformes (vérifiées ✅)

| Catégorie | Nb entrées vérifiées | Résultat |
|---|---|---|
| Table 3.6 λ_DU (17 équipements) | 17 | ✅ 100% OK |
| Table 3.7 λ_DU + DC subsea input (5) | 10 | ✅ 100% OK |
| Table 3.8 λ_DU subsea logic (5) | 5 | ✅ 100% OK |
| Table 3.9 λ_DU subsea final (6) | 6 | ✅ 100% OK |
| Table 3.10 λ_DU downhole (8) | 8 | ✅ 100% OK |
| Table 3.11 λ_DU drilling (8) | 8 | ✅ 100% OK |
| Table 3.12 β (25 équipements) | 25 | ✅ 100% OK |
| Table 3.14 RHF (28 équipements in-table) | 28 | ✅ 100% OK |
| Table 3.15 λ_DU + 70% + IC 90% topside input (16) | 64 | ✅ 100% OK |
| Table 3.16 λ_DU + 70% + IC 90% topside final (19) | 57 | ✅ 100% OK |
| Table 3.17 subsea 70% + IC 90% (11) | 22 | ✅ 100% OK |
| Table 3.18 downhole 70% + IC 90% (9) | 18 | ✅ 100% OK |

### 3.2 Erreurs corrigées (v0.7.1 → v0.7.2)

#### Erreur E1 — `gas_lift_valve_glv.lambda_DU_70` incorrect

| Champ | Avant (v0.7.1) | Après (v0.7.2) | Source |
|---|---|---|---|
| `gas_lift_valve_glv.lambda_DU_70` | 13.2×10⁻⁶/h | **14.0×10⁻⁶/h** | Table 3.18, p45 |

**Origine :** Transcription erronée (13.2 au lieu de 14).

---

#### Erreurs E2+E3 — RHF fabriqués pour `position_switch` et `aspirator_system_flow_switch`

| Clé | Champ | Avant (v0.7.1) | Après (v0.7.2) | Justification |
|---|---|---|---|---|
| `position_switch` | `RHF` | 0.60 | **None** | Absent de Table 3.14 |
| `aspirator_system_flow_switch` | `RHF` | 0.60 | **None** | Absent de Table 3.14 |

**Origine :** Valeurs inventées lors d'une session sans document source disponible.  
**Règle appliquée :** Toute valeur RHF non présente dans Table 3.14 est `None`. Ne pas extrapoler sans documentation explicite.

> Table 3.14 (p37) couvre : transmetteurs (level/pressure/flow/temp), détecteurs F&G, pushbuttons, logique (PLC/PSS/hardwired), vannes (ESV/XV, blowdown, HIPPS/riser, PSV, solenoid, process control, deluge), dampers F&G, circuit breakers/relays. Les switches de position et aspirateurs **ne figurent pas** dans cette table.

---

#### Erreur E4 — `temperature_transmitter_thermocouple` manquant

Dossier §4.2.5 (p55) documente un sous-type "Thermocouple" distinct :

| Champ | Valeur | Source |
|---|---|---|
| `lambda_DU` | 0.10×10⁻⁶/h | Dossier §4.2.5, "Measuring principle: Thermocouple" |
| `lambda_DU_70` | 0.30×10⁻⁶/h | §4.2.5 |
| `lambda_DU_90_lo` | 0.03×10⁻⁶/h | §4.2.5 |
| `lambda_DU_90_hi` | 0.46×10⁻⁶/h | §4.2.5 |
| `DC` | 0.70 | §3.5.2 |
| `beta` | 0.10 | Table 3.12 |
| `RHF` | 0.30 | Table 3.14 (temperature transmitters) |
| Population | 407 tags, 7 installations, 4 opérateurs, 2009–2019, T=1.4×10⁷ h, 2 DU obs. | §4.2.5 |

**Remarque :** λ_DU identique à la valeur générique (0.1). L'IC 90% est très large [0.03–0.46] du fait du faible nombre d'observations (2 DU). Utiliser la valeur générique `temperature_transmitter` si ce niveau de détail n'est pas justifié.

---

### 3.3 Incohérence interne du handbook (non-erreur code)

#### `position_switch.DC` — §3.5.2 vs Dossier §4.2.1

| Source | DC suggéré |
|---|---|
| §3.5.2 texte ("Switches") | 10% |
| Dossier §4.2.1 ("Coverage/Other") | **5%** |

**Résolution :** Le dossier spécifique (§4.2.1) est la source primaire — il documente la valeur réelle utilisée pour calculer les λ_DD/λ_DU publiés. Le texte §3.5.2 est une règle générale plus ancienne. **DC=0.05 est retenu.**

Cette incohérence est signalée dans le champ `notes` de l'entrée `position_switch`.

---

## 4. État final v0.7.2

| Catégorie | Entrées |
|---|---|
| topside_input | 14 (+1 thermocouple) |
| topside_detector | 8 |
| control_logic | 11 |
| topside_valve | 21 |
| topside_final | 17 |
| subsea_input | 5 |
| subsea_logic | 5 |
| subsea_valve | 6 |
| downhole | 12 |
| drilling | 8 |
| **TOTAL** | **107** |

---

## 5. Conformité démarche

| Règle | Respecté |
|---|---|
| Aucune valeur inventée | ✅ (E2+E3 corrigées) |
| Vérification avant modification | ✅ (script systématique) |
| Source primaire citée pour chaque valeur | ✅ |
| Markdown rédigé avant modification code | ✅ |
| Signalement incohérence handbook | ✅ (§3.5.2 vs §4.2.1 DC) |

---

## 6. Scope restant Sprint G

Pages 56–216 (Chapitre 4, dossiers détaillés §4.2.6 à §4.7) non encore reçues.  
À intégrer par tranches de 30 pages au fur et à mesure de leur réception.
