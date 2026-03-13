# 11 — Sprint G : Base de données λ (v0.7.0)
## PRISM SIL Engine — Lambda Database PDS 2021

**Source :** PDS Data Handbook, 2021 Edition — SINTEF Digital, Trondheim, mai 2021  
**Fichier Python :** `packages/sil-py/sil_engine/lambda_db.py`  
**Statut :** ✅ Pages 4–55 intégrées (Tables 3.1–3.18 + §Chap.4 sous-types) | 🔄 Pages 56–216 à venir  
**Version :** v0.7.1 — 106 équipements indexés

---

## Conventions

| Notation | Définition |
|---|---|
| λ_DU | Taux de défaillance dangereuse non détectée [1/h] — **paramètre principal PRISM** |
| λ_DD | λ_D − λ_DU (calculé automatiquement) |
| λ_D | Taux total de défaillances dangereuses |
| λ_S | Taux de défaillances sûres (spurious) |
| λ_DU⁷⁰ | Borne supérieure à 70% de λ_DU (indicateur d'incertitude) |
| λ_DU [90%] | Intervalle de confiance à 90% : [λ_DU_90_lo, λ_DU_90_hi] (Tables 3.15–3.18) |
| DC | Couverture diagnostique (0–1) |
| SFF | Safe Failure Fraction (0–1) |
| β | Facteur de cause commune (Table 3.12) |
| **RHF** | **Random Hardware Failure Fraction (Table 3.14)** — part des λ_DU due à des défaillances aléatoires matérielles (vs systématiques). Utilisé pour Route 2H IEC 61508. |

> **Toutes les valeurs sont en [1/h].** Les tableaux PDS expriment les λ en ×10⁻⁶/h — la conversion est appliquée dans `lambda_db.py`.

> **Note PRISM :** Les calculs PFH/PFD utilisent les formules PRISM corrigées (Moteurs 1 et 2, Bug #11 fix). Les valeurs λ PDS sont des données de terrain indépendantes — elles ne sont pas affectées par les formules de calcul PDS.

---

## Facteurs C_MooN (Table 2.2)

β_MooN = β × C_MooN

| M \ N | N=2 | N=3 | N=4 | N=5 | N=6 |
|---|---|---|---|---|---|
| M=1 | 1.0 | 0.5 | 0.3 | 0.2 | 0.15 |
| M=2 | — | 2.0 | 1.1 | 0.8 | 0.6 |
| M=3 | — | — | 2.8 | 1.6 | 1.2 |
| M=4 | — | — | — | 3.6 | 1.9 |
| M=5 | — | — | — | — | 4.5 |

---

## Table 3.1 — Transmetteurs et switches topside

Valeurs en ×10⁻⁶/h

| Équipement | Clé DB | λ_DU | λ_D | DC | SFF | β | §PDS |
|---|---|---|---|---|---|---|---|
| Position switch | `position_switch` | 1.1 | 1.2 | 5% | 41% | 0.10 | 4.2.1 |
| Aspirator + flow switch | `aspirator_system_flow_switch` | 2.5 | 2.6 | 5% | 46% | 0.10 | 4.2.2 |
| Pressure transmitter | `pressure_transmitter` | 0.48 | 1.36 | 65% | 75% | 0.10 | 4.2.3 |
| Pressure TX — piezorésistif | `pressure_transmitter_piezoresistive` | **0.20** | — | 65% | 75% | 0.10 | 4.2.3 |
| Level transmitter (générique) | `level_transmitter` | 1.9 | 6.3 | 70% | 82% | 0.10 | 4.2.4 |
| Level TX — displacer | `level_transmitter_displacer` | **0.70** | — | 70% | 82% | 0.10 | 4.2.4 |
| Level TX — diff. pressure | `level_transmitter_diff_pressure` | **3.2** | — | 70% | 82% | 0.10 | 4.2.4 |
| Level TX — radar | `level_transmitter_radar` | **2.7** | — | 70% | 82% | 0.10 | 4.2.4 |
| Level TX — nuclear (gamma) | `level_transmitter_nuclear` | **4.1** | — | 70% | 82% | 0.10 | 4.2.4 |
| Temperature transmitter | `temperature_transmitter` | 0.1 | 0.4 | 70% | 82% | 0.10 | 4.2.5 |
| Flow transmitter | `flow_transmitter` | 1.4 | 4.0 | 65% | 79% | 0.10 | 4.2.6 |

> ⚠️ Level transmitter : utiliser le sous-type par principe de mesure si connu — les écarts sont significatifs (displacer 0.70 vs nuclear 4.1×10⁻⁶/h).

---

## Table 3.2 — Détecteurs topside

Valeurs en ×10⁻⁶/h

| Équipement | Clé DB | λ_DU | λ_D | DC | SFF | β | RHF | §PDS |
|---|---|---|---|---|---|---|---|---|
| Catalytic point gas detector | `catalytic_point_gas_detector` | 1.5 | 3.6 | 60% | 72% | 0.10 | 0.60 | 4.2.7 |
| IR point gas detector | `ir_point_gas_detector` | **0.25** ~~0.30~~ | 1.7 | 85% | 92% | 0.10 | 0.40 | 4.2.8 |
| Aspirated IR gas detector system | `aspirated_ir_point_gas_detector` | 2.9 | 3.5 | 16% | 56% | 0.10 | 0.40 | 4.2.9 |
| Line gas detector | `line_gas_detector` | **0.44** ~~0.40~~ | 4.4 | 90% | 94% | 0.10 | 0.40 | 4.2.10 |
| Electrochemical detector | `electrochemical_detector` | 1.7 | 4.2 | 60% | 68% | 0.10 | 0.40 | 4.2.11 |
| Smoke detector | `smoke_detector` | 0.16 | 0.8 | 80% | 92% | 0.10 | 0.60 | 4.2.12 |
| Heat detector | `heat_detector` | 0.37 | 0.92 | 60% | 84% | 0.10 | 0.60 | 4.2.13 |
| Flame detector | `flame_detector` | 0.35 | 1.41 | 75% | 90% | 0.10 | 0.40 | 4.2.14 |

---

## Table 3.3 — Boutons / Call points

Valeurs en ×10⁻⁶/h

| Équipement | Clé DB | λ_DU | λ_D | DC | SFF | β | §PDS |
|---|---|---|---|---|---|---|---|
| Manual pushbutton (outdoor) | `manual_pushbutton_outdoor` | 0.19 | 0.23 | 20% | 46% | 0.05 | 4.2.15 |
| CAP switch (indoor) | `cap_switch_indoor` | 0.11 | 0.14 | 20% | 46% | 0.05 | 4.2.16 |

---

## Table 3.4 — Unités de logique topside

Valeurs en ×10⁻⁶/h. λ_DU⁷⁰ non disponible pour les unités logiques.

| Équipement | Clé DB | λ_DU | λ_D | DC | SFF | β | §PDS |
|---|---|---|---|---|---|---|---|
| **PLC standard — Entrée analogique** | `std_plc_analog_input` | 0.7 | 1.8 | 60% | 80% | 0.07 | 4.3.1.1 |
| **PLC standard — CPU/solveur (1oo1)** | `std_plc_cpu` | 3.5 | 8.8 | 60% | 80% | 0.07 | 4.3.1.2 |
| **PLC standard — Sortie digitale** | `std_plc_digital_output` | 0.7 | 1.8 | 60% | 80% | 0.07 | 4.3.1.3 |
| **PSS — Entrée analogique** | `pss_analog_input` | 0.1 | 1.4 | 90% | 95% | 0.05 | 4.3.2.1 |
| **PSS — CPU/solveur (1oo1)** | `pss_cpu` | 0.3 | 2.7 | 90% | 95% | 0.05 | 4.3.2.2 |
| **PSS — Sortie digitale** | `pss_digital_output` | 0.16 | 1.60 | 90% | 95% | 0.05 | 4.3.2.3 |
| **Hardwired — Entrée/Trip amp.** | `hardwired_analog_input` | 0.04 | 0.04 | 0% | 91% | 0.03 | 4.3.3.1 |
| **Hardwired — Logique (1oo1)** | `hardwired_logic` | 0.03 | 0.03 | 0% | 91% | 0.03 | 4.3.3.2 |
| **Hardwired — Sortie digitale** | `hardwired_digital_output` | 0.04 | 0.04 | 0% | 91% | 0.03 | 4.3.3.3 |
| Fire central incl. I/O | `fire_central` | 0.7 | 6.6 | 90% | 95% | 0.05 | 4.3.4.1 |
| Galvanic barrier | `galvanic_barrier` | 0.1 | 0.1 | 0% | 50% | — | 4.3.4.2 |

> ⚠️ Hardwired DC=0 : hypothèse que toute défaillance DD conduit à un trip (action sûre). Voir §4.3.3.

---

## Table 3.5 — Vannes topside

Valeurs en ×10⁻⁶/h

| Équipement | Clé DB | λ_DU | λ_D | DC | SFF | β | §PDS |
|---|---|---|---|---|---|---|---|
| Topside ESV/XV — générique | `topside_esv_xv` | 2.3 | 2.5 | 5% | 48% | 0.08 | 4.4.1 |
| Topside ESV/XV — ball valve | `topside_esv_xv_ball` | 2.1 | 2.2 | 5% | 48% | 0.08 | 4.4.1.1 |
| Topside ESV/XV — gate valve | `topside_esv_xv_gate` | 3.3 | 3.5 | 5% | 48% | 0.08 | 4.4.1.2 |
| Riser ESV | `riser_esv` | 1.9 | 2.0 | 5% | 48% | 0.08 | 4.4.2 |
| XT PMV/PWV | `topside_xt_pmv_pwv` | 2.3 | 2.5 | 5% | 48% | 0.08 | 4.4.3 |
| XT HASCV | `topside_xt_hascv` | 4.2 | 4.5 | 5% | 48% | 0.08 | 4.4.4 |
| XT GLESDV | `topside_xt_glesdv` | 0.2 | 0.2 | 5% | 48% | 0.08 | 4.4.5 |
| XT CIESDV | `topside_xt_ciesdv` | 1.8 | 1.9 | 5% | 48% | 0.08 | 4.4.6 |
| HIPPS valve | `topside_hipps_valve` | 0.5 | 0.5 | 5% | 57% | 0.08 | 4.4.7 |
| Blowdown valve | `blowdown_valve` | 2.8 | 3.1 | 5% | 48% | 0.08 | 4.4.8 |
| Fast opening valve (FOV) | `fast_opening_valve_fov` | 6.3 | 6.6 | 5% | 41% | 0.08 | 4.4.9 |
| Solenoid/pilot valve (simple) | `solenoid_pilot_valve` | 0.3 | 0.3 | 5% | 62% | 0.10 | 4.4.10 |
| Vanne de contrôle (opérée fréq.) | `process_control_valve_frequent` | 2.5 | 3.6 | 30% | 60% | 0.08 | 4.4.11 |
| Vanne de contrôle (arrêt seul) | `process_control_valve_shutdown` | 3.5 | — | 5% | 60% | 0.08 | 4.4.11 |
| PSV | `pressure_relief_valve_psv` | 1.9 | 1.9 | 0% | 33% | 0.07 | 4.4.12 |
| Deluge valve | `deluge_valve` | 1.4 | 1.4 | 0% | 37% | 0.08 | 4.4.13 |
| Fire water monitor valve | `fire_water_monitor_valve` | 2.2 | 2.2 | 0% | 37% | 0.08 | 4.4.14 |
| Water mist valve | `water_mist_valve` | 0.8 | 0.8 | 0% | 37% | 0.08 | 4.4.16 |
| Sprinkler valve | `sprinkler_valve` | 1.3 | 1.3 | 0% | 38% | 0.08 | 4.4.17 |
| Foam valve | `foam_valve` | 4.1 | 4.1 | 0% | 37% | 0.08 | 4.4.18 |
| Ballast water valve | `ballast_water_valve` | 0.5 | 0.6 | 5% | 43% | 0.08 | 4.4.19 |

> ⚠️ ESV/XV : λ_DU = 2.3 pour vanne avec critère d'étanchéité (tight shut-off). Sans critère : λ_DU = 2.0×10⁻⁶.  
> ⚠️ Solénoïde : pour configuration avec solénoïde ET pilote sur la même vanne, λ_DU total = 0.6×10⁻⁶/h.  
> ⚠️ SFF < 60% sur la plupart des vannes → question Route 2H (IEC 61508-2 §7.4.4) pour SIL 2. Voir §3.1.3.

---

## Table 3.6 — Éléments finaux divers (topside)

Valeurs en ×10⁻⁶/h

| Équipement | Clé DB | λ_DU | λ_D | DC | SFF | §PDS |
|---|---|---|---|---|---|---|
| Fire water monitor | `fire_water_monitor` | 1.5 | 1.5 | 0% | 0% | 4.4.15 |
| Pompe FW — diesel électrique | `fire_water_pump_diesel_electric` | 25 | 25 | 0% | 10% | 4.4.20 |
| Pompe FW — diesel hydraulique | `fire_water_pump_diesel_hydraulic` | 21 | 21 | 0% | 10% | 4.4.21 |
| Pompe FW — diesel mécanique | `fire_water_pump_diesel_mechanical` | 14 | 14 | 0% | 10% | 4.4.22 |
| Fire & gas damper | `fire_gas_damper` | 3.1 | 3.1 | 0% | 42% | 4.4.23 |
| Rupture disc | `rupture_disc` | 0.1 | 0.1 | 0% | 50% | 4.4.24 |
| Circuit breaker | `circuit_breaker` | 0.4 | 0.4 | 0% | 60% | 4.4.25 |
| Relay / contactor | `relay_contactor` | 0.1 | 0.1 | 0% | 60% | 4.4.26 |
| Fire door | `fire_door` | 2.7 | 2.7 | 0% | 42% | 4.4.27 |
| Watertight door | `watertight_door` | 3.0 | 3.0 | 0% | 42% | 4.4.28 |
| Emergency generator | `emergency_generator` | 8.6 | 8.6 | 0% | 10% | 4.4.29 |
| Lifeboat engines | `lifeboat_engines` | 11 | 11 | 0% | 10% | 4.4.30 |
| UPS & battery package | `ups_battery_package` | 0.5 | 2.6 | 80% | 80% | 4.4.31 |
| Emergency lights | `emergency_lights` | 3.7 | 3.7 | 0% | 0% | 4.4.32 |
| Flashing beacons | `flashing_beacons` | 0.2 | 0.2 | 0% | 0% | 4.4.33 |
| Lifeboat radio | `lifeboat_radio` | 12 | 12 | 0% | 0% | 4.4.34 |
| PA loudspeakers | `pa_loudspeakers` | 0.2 | 0.2 | 0% | 0% | 4.4.35 |

---

## Tables 3.7–3.8 — Capteurs et logique subsea

Valeurs en ×10⁻⁶/h. β non spécifié pour le subsea — utiliser valeurs topside analogues.  
DC et SFF **indicatifs uniquement** pour équipements subsea.

| Équipement | Clé DB | λ_DU | λ_D | DC | SFF | §PDS |
|---|---|---|---|---|---|---|
| Subsea pressure sensor | `subsea_pressure_sensor` | 0.4 | 1.2 | 65% | 79% | 4.5.1 |
| Subsea temperature sensor | `subsea_temperature_sensor` | 0.2 | 0.6 | 65% | 79% | 4.5.2 |
| Subsea P+T sensor (combiné) | `subsea_pressure_temperature_sensor` | 0.4 | 1.3 | 70% | 82% | 4.5.3 |
| Subsea flow sensor | `subsea_flow_sensor` | 1.3 | 3.7 | 65% | 79% | 4.5.4 |
| Subsea sand detector | `subsea_sand_detector` | 2.0 | 5.7 | 65% | 79% | 4.5.5 |
| MCS Master control station | `subsea_mcs` | 3.1 | 7.7 | 60% | 80% | 4.5.6 |
| Umbilical hydraulique/chimique | `umbilical_hydraulic_chemical` | 0.06 | 0.30 | 80% | 90% | 4.5.7 |
| Umbilical électrique/signal | `umbilical_power_signal` | 0.06 | 0.28 | 80% | 90% | 4.5.8 |
| SEM subsea electronic module | `subsea_sem` | 1.1 | 2.6 | 60% | 80% | 4.5.9 |
| Subsea solenoid control valve | `subsea_solenoid_control_valve` | 0.2 | 0.2 | 0% | 60% | 4.5.10 |

---

## Table 3.9 — Vannes subsea finales

Valeurs en ×10⁻⁶/h. SFF non fourni pour les éléments finaux subsea.

| Équipement | Clé DB | λ_DU | λ_D | DC | §PDS |
|---|---|---|---|---|---|
| Manifold isolation valve | `subsea_manifold_isolation_valve` | 0.2 | 0.2 | 0% | 4.5.11 |
| XT PMV/PWV | `subsea_xt_pmv_pwv` | 0.6 | 0.6 | 0% | 4.5.12 |
| XT XOV (crossover) | `subsea_xt_xov` | 0.08 | 0.08 | 0% | 4.5.13 |
| XT AMV (annulus master) | `subsea_xt_amv` | 0.12 | 0.12 | 0% | 4.5.14 |
| XT CIV/MIV (injection) | `subsea_xt_civ_miv` | 0.24 | 0.24 | 0% | 4.5.15 |
| SSIV subsea isolation | `subsea_ssiv` | 0.4 | 0.4 | 0% | 4.5.16 |

---

## Table 3.10 — Équipements downhole / well completion

Valeurs en ×10⁻⁶/h. DC=0% et SFF non fournis.

| Équipement | Clé DB | λ_DU | λ_D | §PDS |
|---|---|---|---|---|
| DHSV générique | `dhsv_generic` | 7.5 | 7.5 | 4.6.1 |
| DHSV TRSCSSV | `dhsv_trscssv` | 4.0 | 4.0 | 4.6.2 |
| DHSV WRSCSSV | `dhsv_wrscssv` | 15 | 15 | 4.6.3 |
| TRSCASSV type A | `trscassv_type_a` | 3.6 | 3.6 | 4.6.4 |
| TRSCASSV type B | `trscassv_type_b` | 3.9 | 3.9 | 4.6.5 |
| WRCIV (wire retrievable) | `wrciv` | 1.8 | 1.8 | 4.6.6 |
| TRCIV (tubing retrievable) | `trciv` | 0.3 | 0.3 | 4.6.7 |
| Gas lift valve (GLV) | `gas_lift_valve_glv` | 13 | 13 | 4.6.8 |

---

## Table 3.11 — Équipements de forage

Valeurs en ×10⁻⁶/h. λ_DU⁷⁰ et β non disponibles pour le forage.

| Équipement | Clé DB | λ_DU | λ_D | DC | SFF | §PDS |
|---|---|---|---|---|---|---|
| Annular preventer | `annular_preventer` | 9.8 | 9.8 | 0% | 80% | 4.7.1 |
| Ram preventer | `ram_preventer` | 3.4 | 3.4 | 0% | 10% | 4.7.2 |
| Choke and kill valve | `choke_kill_valve` | 0.8 | 0.8 | 0% | 20% | 4.7.3 |
| Choke and kill line | `choke_kill_line` | 22 | 22 | 0% | 10% | 4.7.4 |
| Hydraulic connector | `hydraulic_connector` | 3.1 | 3.1 | 0% | 25% | 4.7.5 |
| Multiplex control system ¹ | `multiplex_control_system` | 62 | 124 | 50% | 50% | 4.7.6 |
| Pilot control system | `pilot_control_system` | 102 | 102 | 0% | 0% | 4.7.7 |
| Acoustic backup control | `acoustic_backup_control` | 37 | 37 | 0% | 0% | 4.7.8 |

> ¹ Multiplex : taux total pour TOUTES les fonctions (pods redondants inclus). Pour un pod individuel, utiliser ≈ λ_DU/2.

---

## Table 3.12 — Valeurs β génériques (topside)

| Groupe d'équipements | β |
|---|---|
| Process transmitters | **0.10** |
| Process switches | **0.10** |
| Fire & gas detectors | **0.10** |
| Pushbuttons / call points | **0.05** |
| Standard industrial PLCs | **0.07** |
| Programmable safety systems | **0.05** |
| Hardwired safety systems | **0.03** |
| Topside shutdown valves | **0.08** |
| Blowdown & fast opening valves | **0.08** |
| Solenoid/pilot valves (même vanne) | **0.10** |
| Solenoid/pilot valves (vannes diff.) | **0.07** |
| Process control valves | **0.08** |
| Pressure relief valves (PSV) | **0.07** |
| Deluge valves | **0.08** |
| Fire & gas dampers | **0.12** |
| Circuit breakers/contactors/relays | **0.05** |

> Note PDS : les données de terrain ([3]) indiquent que les β réels pourraient être **supérieurs** pour les transmetteurs process, les détecteurs gaz, les vannes d'arrêt et les clapets coupe-feu.

---

## Table 3.14 — RHF (Random Hardware Failure Fraction)

Le RHF est la fraction de λ_DU attribuable à des défaillances aléatoires matérielles (vs systématiques ou humaines). Utilisé pour justifier le SIL par la **Route 2H** (IEC 61508-2 §7.4.4).

λ_DU_hardware = RHF × λ_DU

| Catégorie d'équipement | RHF typique |
|---|---|
| Hardwired (trip amplifiers, logic, output) | **0.80** |
| Pushbuttons / call points | **0.60** |
| Smoke / heat detectors | **0.60** |
| Circuit breakers, relays | **0.60** |
| IR / line / electrochemical / flame gas detectors | **0.40** |
| PSS (programmable safety systems) | **0.40** |
| Process control valves | **0.40** |
| Pressure relief valves, deluge, F&W valves | **0.50** |
| Pressure / temperature / flow transmitters | **0.30** |
| Topside shutdown & blowdown valves | **0.30** |
| Riser ESV | **0.50** |
| HIPPS valve | **0.50** |
| Standard PLCs | **0.10** |
| Level transmitters | **0.20** |

> ⚠️ RHF non disponible pour équipements subsea, downhole et forage.

---

## Tables 3.15–3.18 — Intervalles de confiance à 90%

Les IC 90% sont stockés dans les champs `lambda_DU_90_lo` et `lambda_DU_90_hi` de chaque entrée. Ils reflètent l'incertitude statistique sur les données de terrain. Un IC large signale une **expérience opérationnelle limitée** — à traiter avec prudence.

Exemples notables (×10⁻⁶/h) :

| Équipement | λ_DU (best est.) | IC 90% bas | IC 90% haut | Rapport hi/lo |
|---|---|---|---|---|
| Pressure transmitter | 0.48 | 0.37 | 0.61 | 1.6 |
| IR point gas detector | 0.25 | 0.21 | 0.30 | 1.4 |
| Topside ESV/XV générique | 2.3 | 1.9 | 2.8 | 1.5 |
| Circuit breaker | 0.4 | 0.02 | 2.1 | **105** ← données limitées |
| Sprinkler valve | 1.3 | 0.5 | 8.3 | **17** ← forte incertitude |
| Emergency generator | 8.6 | 3.4 | 18.0 | 5.3 |
| DHSV TRSCSSV topside | 6.2 | 5.7 | 6.7 | 1.2 ← données solides |
| DHSV WRSCSSV subsea | 4.8 | 2.1 | 10.0 | 4.8 |
| TRSCASSV type A | 3.6 | 3.0 | 4.4 | 1.5 |

---

## Corrections v0.7.0 → v0.7.1

| Clé | Champ | Ancienne valeur | Nouvelle valeur | Source |
|---|---|---|---|---|
| `ir_point_gas_detector` | λ_DU | 0.30×10⁻⁶ | **0.25×10⁻⁶** | §4.2.8 tableau détaillé |
| `line_gas_detector` | λ_DU | 0.40×10⁻⁶ | **0.44×10⁻⁶** | §4.2.10 tableau détaillé |
| `pa_loudspeakers` | λ_DU | 0.20×10⁻⁶ | **0.23×10⁻⁶** | §4.4.35 tableau détaillé |
| `circuit_breaker` | λ_DU_70 | None | **1.1×10⁻⁶** | Table 3.16 |
| `process_control_valve_shutdown` | λ_DU_70 | 5.5×10⁻⁶ | confirmé 5.5×10⁻⁶ | Table 3.16 |

---

## Nouvelles entrées v0.7.1

### Level transmitter — sous-types par principe de mesure (§4.2.4)

| Clé DB | Principe | λ_DU ×10⁻⁶ | IC 90% [lo, hi] | RHF |
|---|---|---|---|---|
| `level_transmitter_displacer` | Displacer | **0.70** | [0.2, 1.9] | 0.20 |
| `level_transmitter_diff_pressure` | Pression différentielle | **3.2** | [2.2, 4.6] | 0.20 |
| `level_transmitter_radar` | Radar (free space) | **2.7** | [1.2, 5.4] | 0.20 |
| `level_transmitter_nuclear` | Nuclear (gamma) | **4.1** | [1.4, 9.4] | 0.20 |

> Le sous-type `level_transmitter` (générique, λ_DU=1.9) reste disponible si le principe de mesure est inconnu.

### Pressure transmitter — sous-type piezorésistif (§4.2.3)

| Clé DB | λ_DU ×10⁻⁶ | IC 90% [lo, hi] | Note |
|---|---|---|---|
| `pressure_transmitter_piezoresistive` | **0.20** | [0.01, 0.74] | 1 seule observation — IC très large |

### DHSV — sous-types par localisation du puits (§4.6.2–4.6.3)

| Clé DB | Type | Localisation | λ_DU ×10⁻⁶ | IC 90% |
|---|---|---|---|---|
| `dhsv_trscssv_topside` | TRSCSSV | Topside | **6.2** | [5.7, 6.7] |
| `dhsv_trscssv_subsea` | TRSCSSV | Subsea | **1.55** | [1.3, 1.8] |
| `dhsv_wrscssv_topside` | WRSCSSV | Topside | **15.0** | [14.0, 17.0] |
| `dhsv_wrscssv_subsea` | WRSCSSV | Subsea | **4.8** | [2.1, 10.0] |

> La localisation (topside vs subsea) a un impact majeur : TRSCSSV subsea = 4× moins de défaillances qu'en topside. À utiliser dès que le type de puits est connu.

---

## Usage PRISM

```python
from lambda_db import get_lambda, make_subsystem_params

# Récupérer une entrée
e = get_lambda("pressure_transmitter")
print(f"λ_DU = {e.lambda_DU:.3e} /h")   # → 4.800e-07 /h
print(f"DC   = {e.DC:.0%}")              # → 65%

# Construire SubsystemParams
params = make_subsystem_params(
    entry=e,
    T1=8760.0,       # intervalle de test annuel [h]
    MTTR=8.0,        # temps de réparation [h]
    architecture="1oo2",
    M=1, N=2,
)
from sil_engine import SubsystemParams, route_compute
sp = SubsystemParams(**params)
result = route_compute(sp)

# Lister les équipements d'une catégorie
from lambda_db import list_equipment
for item in list_equipment("topside_valve"):
    print(f"{item.key:<40} λ_DU={item.lambda_DU:.2e}")

# Recherche par mot-clé
from lambda_db import search_equipment
results = search_equipment("gas detector")
```

---

## Roadmap Sprint G

| Tâche | Statut |
|---|---|
| Tables 3.1–3.12 (pages 4–24) | ✅ **v0.7.0** |
| Tables 3.13–3.18 + RHF + IC 90% (pages 25–55) | ✅ **v0.7.1** |
| Corrections λ_DU (IR gas, line gas, PA loudspeakers) | ✅ **v0.7.1** |
| Level TX sous-types ×4 + pressure TX piezorésistif | ✅ **v0.7.1** |
| DHSV sous-types topside/subsea ×4 | ✅ **v0.7.1** |
| Chapitre 4 — Dossiers détaillés restants (pages 56–216) | 🔄 Tranches suivantes |
| Tests T47–T5x (groupe L) | ⏳ Après intégration Chap. 4 |
| `get_lambda()` avec filtrage par environnement/dimension | ⏳ Chap. 4 requis |
| Documentation INERIS (traçabilité sources) | ✅ Ce fichier |

---

## Références

| Réf. | Document |
|---|---|
| [PDS2021] | SINTEF Digital, *PDS Data Handbook, 2021 Edition*, Trondheim, mai 2021 |
| [IEC61508-6] | IEC 61508-6:2010, Annex B — Markov modelling, Table D.5 (C_MooN) |
| [NOROG070] | Norwegian Oil and Gas Association, Guideline 070, §8.5 |
