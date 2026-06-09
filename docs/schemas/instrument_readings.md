# Schema: instrument_readings

- id: UUID
- upload_id: UUID
- instrument_type: string
- sample_id: string
- geom: geometry(Point, EPSG:4326)
- data: JSONB
- flagged: boolean
- flag_reasons: text[]
- uploaded_at: timestamptz
