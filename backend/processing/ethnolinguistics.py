from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

SENSITIVE_KNOWLEDGE_LEVELS = {"public", "community_restricted", "sacred_or_sensitive"}
DEFAULT_LANGUAGE_HINTS = {
    "sw": "Swahili",
    "luo": "Dholuo",
    "kam": "Kamba",
    "kik": "Gikuyu",
    "en": "English",
}
GEO_TERM_LEXICON = {
    "shaba": {"concept": "copper", "domain": "mineral", "confidence": 0.86},
    "dhahabu": {"concept": "gold", "domain": "mineral", "confidence": 0.86},
    "maji": {"concept": "water", "domain": "hydrogeology", "confidence": 0.8},
    "chumvi": {"concept": "salinity", "domain": "hydrogeology", "confidence": 0.74},
    "maua": {
        "concept": "flower_or_indicator_plant",
        "domain": "geobotany",
        "confidence": 0.7,
    },
    "mlima": {
        "concept": "hill_or_mountain",
        "domain": "geomorphology",
        "confidence": 0.72,
    },
    "mawe": {"concept": "rock", "domain": "geology", "confidence": 0.68},
}


@dataclass(frozen=True)
class CommunityConsent:
    community_id: str
    consent_scope: str
    attribution_text: str
    sensitivity: str = "community_restricted"

    def as_dict(self) -> dict:
        if self.sensitivity not in SENSITIVE_KNOWLEDGE_LEVELS:
            raise ValueError(f"unsupported sensitivity: {self.sensitivity}")
        return {
            "community_id": self.community_id,
            "consent_scope": self.consent_scope,
            "attribution_text": self.attribution_text,
            "sensitivity": self.sensitivity,
        }


def normalise_term(term: str) -> str:
    return " ".join(term.lower().strip().replace("-", " ").split())


def record_ethnolinguistic_term(payload: dict) -> dict:
    term = normalise_term(payload.get("term", ""))
    language_code = payload.get("language_code", "und")
    consent = CommunityConsent(
        community_id=payload.get("community_id", "unknown_community"),
        consent_scope=payload.get("consent_scope", "project_internal"),
        attribution_text=payload.get(
            "attribution_text", "Community knowledge contributor"
        ),
        sensitivity=payload.get("sensitivity", "community_restricted"),
    ).as_dict()
    inferred = interpret_local_term(term, language_code)
    return {
        "term_id": f"ethno-{abs(hash((term, language_code))) % 1_000_000:06d}",
        "term": term,
        "language_code": language_code,
        "language_name": DEFAULT_LANGUAGE_HINTS.get(language_code, "Undetermined"),
        "literal_translation": payload.get("literal_translation"),
        "inferred": inferred,
        "consent": consent,
        "location": {"lon": payload.get("lon"), "lat": payload.get("lat")},
        "linked_project_id": payload.get("project_id"),
    }


def interpret_local_term(term: str, language_code: str = "und") -> dict:
    normalised = normalise_term(term)
    matches = []
    for token in normalised.split():
        if token in GEO_TERM_LEXICON:
            matches.append({"token": token, **GEO_TERM_LEXICON[token]})
    if not matches and normalised in GEO_TERM_LEXICON:
        matches.append({"token": normalised, **GEO_TERM_LEXICON[normalised]})
    top_match = max(matches, key=lambda match: float(match["confidence"]), default=None)
    top_domain = top_match["domain"] if top_match else "unknown"
    confidence = float(top_match["confidence"]) if top_match else 0.0
    return {
        "input_term": normalised,
        "language_code": language_code,
        "matches": matches,
        "top_domain": top_domain,
        "confidence": round(confidence, 3),
        "recommended_action": _recommended_action(top_domain),
    }


def _recommended_action(domain: str) -> str:
    return {
        "mineral": "cross-check local term against XRF/pathfinder anomalies before disclosure",
        "hydrogeology": "compare local water term with borehole, spring, salinity, and groundwater layers",
        "geobotany": "link term to indicator plant observation with community attribution",
        "geomorphology": "compare to DEM, lineaments, and geological map units",
        "geology": "field-check outcrop or lithology interpretation",
    }.get(domain, "request geologist and community review")


def toponym_analysis(features: list[dict]) -> dict:
    interpreted = []
    for feature in features:
        name = feature.get("name", "")
        language_code = feature.get("language_code", "und")
        interpreted.append(
            {
                "name": name,
                "language_code": language_code,
                "interpretation": interpret_local_term(name, language_code),
                "geometry": feature.get("geometry"),
            }
        )
    domain_counts = Counter(
        item["interpretation"]["top_domain"] for item in interpreted
    )
    return {
        "feature_count": len(features),
        "domain_counts": dict(domain_counts),
        "interpreted_features": interpreted,
        "layer_url": "minio://ethnolinguistics/toponym_interpretations.geojson",
    }


def community_attribution_report(records: list[dict]) -> dict:
    community_counts = Counter(
        record.get("community_id", "unknown_community") for record in records
    )
    restricted = sum(
        1
        for record in records
        if record.get("sensitivity", "community_restricted") != "public"
    )
    return {
        "record_count": len(records),
        "community_counts": dict(community_counts),
        "restricted_record_count": restricted,
        "report_url": "minio://ethnolinguistics/community_attribution_report.pdf",
        "jorc_notice": "Ethno-linguistic knowledge is contextual and must be consented, attributed, and verified by conventional geoscience evidence.",
    }


def knowledge_layer(records: list[dict], include_restricted: bool = False) -> dict:
    visible = [
        record
        for record in records
        if include_restricted
        or record.get("sensitivity", "community_restricted") == "public"
    ]
    return {
        "visible_record_count": len(visible),
        "redacted_record_count": len(records) - len(visible),
        "geojson_url": "minio://ethnolinguistics/knowledge_layer.geojson",
        "access_policy": (
            "restricted_allowed" if include_restricted else "public_only_redacted"
        ),
    }
