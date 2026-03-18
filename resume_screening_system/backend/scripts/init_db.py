from app.core.database import Base, engine
from app.models.job import Job
from app.models.resume import Resume
from app.models.weight_template import WeightTemplate


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")