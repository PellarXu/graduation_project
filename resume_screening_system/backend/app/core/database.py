from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}?charset=utf8mb4"
)

engine = create_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def bootstrap_schema():
    from app.models.job import Job  # noqa: F401
    from app.models.resume import Resume  # noqa: F401
    from app.models.weight_template import WeightTemplate  # noqa: F401

    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    additive_columns = {
        "resume": {
            "extract_status": "ALTER TABLE resume ADD COLUMN extract_status VARCHAR(20) DEFAULT 'pending'",
            "model_version": "ALTER TABLE resume ADD COLUMN model_version VARCHAR(100) NULL",
            "entity_result": "ALTER TABLE resume ADD COLUMN entity_result JSON NULL",
            "profile_raw": "ALTER TABLE resume ADD COLUMN profile_raw JSON NULL",
            "profile_masked": "ALTER TABLE resume ADD COLUMN profile_masked JSON NULL",
            "sensitive_summary": "ALTER TABLE resume ADD COLUMN sensitive_summary JSON NULL",
            "analyzed_at": "ALTER TABLE resume ADD COLUMN analyzed_at DATETIME NULL",
            "updated_at": "ALTER TABLE resume ADD COLUMN updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        },
        "job": {
            "skill_weight": "ALTER TABLE job ADD COLUMN skill_weight DECIMAL(6,4) DEFAULT 0.2500",
            "experience_weight": "ALTER TABLE job ADD COLUMN experience_weight DECIMAL(6,4) DEFAULT 0.2500",
            "degree_weight": "ALTER TABLE job ADD COLUMN degree_weight DECIMAL(6,4) DEFAULT 0.2500",
            "major_weight": "ALTER TABLE job ADD COLUMN major_weight DECIMAL(6,4) DEFAULT 0.2500",
            "updated_at": "ALTER TABLE job ADD COLUMN updated_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        },
    }

    with engine.begin() as connection:
        for table_name, ddl_map in additive_columns.items():
            if not inspector.has_table(table_name):
                continue

            existing = {item["name"] for item in inspector.get_columns(table_name)}
            for column_name, ddl in ddl_map.items():
                if column_name not in existing:
                    connection.execute(text(ddl))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
