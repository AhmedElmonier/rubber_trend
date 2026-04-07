import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, LatexPrice
from sqlalchemy.exc import IntegrityError

@pytest.fixture
def db_session():
    # Use in-memory SQLite for tests
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_latex_price_model(db_session):
    today = datetime.date.today()
    price_entry = LatexPrice(
        date=today,
        country="TestCountry",
        price=100.5,
        currency_unit="TEST/kg"
    )
    db_session.add(price_entry)
    db_session.commit()
    
    retrieved = db_session.query(LatexPrice).first()
    assert retrieved.country == "TestCountry"
    assert retrieved.price == 100.5
    assert retrieved.date == today

def test_unique_constraint(db_session):
    today = datetime.date.today()
    entry1 = LatexPrice(date=today, country="MarketA", price=10.0, currency_unit="U")
    db_session.add(entry1)
    db_session.commit()
    
    # Adding same date and country should fail
    entry2 = LatexPrice(date=today, country="MarketA", price=12.0, currency_unit="U")
    db_session.add(entry2)
    with pytest.raises(IntegrityError):
        db_session.commit()
