from sqlalchemy import text


make_flow_hypertable = text("""
    text("SELECT create_hypertable('flow.data', by_range('date', INTERVAL '1 year'));")
""")

make_area_view = text("""
    create or replace view flow.area as 
    WITH area_calculated AS (
        SELECT id, 
            "group", 
            ST_Area(ST_Transform(geometry, 5070)) AS sqm
        FROM flow.locations
    )
    SELECT id, 
        "group", 
        sqm, 
        sqm * 10.7639 AS sqft
    FROM area_calculated;
""")

TIMESCALE_SETUP = [make_flow_hypertable, make_area_view]
