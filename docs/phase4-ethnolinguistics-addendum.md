# TERRAFORGE LABS — Phase 4 Ethno-Linguistics Addendum

TerraForge previously had only a narrow indigenous-knowledge field in the geobotany workflow: local plant names and local significance. This addendum makes ethno-linguistics an explicit Phase 4 capability for geological, hydrogeological, geobotanical, environmental, and community-engagement intelligence.

## Purpose

Ethno-linguistics captures how local languages, toponyms, oral place knowledge, and community technical vocabulary encode geoscience observations. Examples include mineral terms, water/salinity terms, plant-indicator names, fault/landform names, sacred or restricted sites, and settlement risk knowledge.

## Core principles

- **Consent first:** every record carries community ID, consent scope, attribution text, and sensitivity.
- **Attribution by design:** reports can credit communities when their knowledge contributes to discovery or risk reduction.
- **Restricted knowledge protection:** sensitive or sacred records are redacted by default from public map layers and investor data rooms.
- **Geoscience verification:** local terms guide follow-up, but all mineral, groundwater, and hazard interpretations require conventional evidence.
- **Multilingual support:** language codes and language names are stored with every term so later LLM translation and review can be audited.

## Track V — Ethno-Linguistics & Community Knowledge

Track V adds a bridge between the Phase 4 geobotany, hydrogeology, urban planning, infrastructure, and gap-closure modules.

### Sub-modules

1. **Local term registry** — records terms, language codes, literal translations, local significance, location, project link, consent scope, and sensitivity.
2. **Geo-term interpretation** — maps local words such as copper, gold, water, salinity, flower, hill, and rock terms to geoscience domains and recommended follow-up.
3. **Toponym analysis** — interprets place names and clusters them into mineral, hydrogeology, geobotany, geomorphology, and geology domains.
4. **Community attribution report** — counts records by contributing community and prepares attribution/disclaimer text for reports.
5. **Ethno-linguistic knowledge layer** — publishes redacted or restricted GeoJSON layers for web/mobile maps.

## API endpoints

- `POST /ethnolinguistics/record-term`
- `POST /ethnolinguistics/interpret-term`
- `POST /ethnolinguistics/toponym-analysis`
- `POST /ethnolinguistics/community-attribution`
- `POST /ethnolinguistics/knowledge-layer`

## Definition of Done

- Local term records preserve language code, inferred geoscience domain, location, consent scope, attribution text, and sensitivity.
- Public knowledge layers redact non-public records by default.
- Toponym analysis returns interpreted features and domain counts.
- Community attribution reports count contributing communities and emit a geoscience-verification notice.
- Ethno-linguistic outputs can be linked to geobotany, hydrogeology, pathfinder targeting, urban risk, and investor data-room redaction workflows.
