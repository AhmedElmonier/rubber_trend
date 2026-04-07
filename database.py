import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class LatexPrice(Base):
    __tablename__ = 'latex_prices'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    country = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    currency_unit = Column(String(20), nullable=False)
    
    # Ensure we only have one price per country per date
    __table_args__ = (UniqueConstraint('date', 'country', name='uq_date_country'),)

# Use DATABASE_URL from env or fallback to local sqlite
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), 'latex_prices.db')
db_url = os.environ.get("DATABASE_URL", f'sqlite:///{DEFAULT_DB_PATH}')

engine = create_engine(db_url, echo=False)

def init_db():
    Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()
