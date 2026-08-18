import pytest
from app.database import SessionLocal, Base, engine

# run on every test function
@pytest.fixture(scope="function")
def db_session():
    """
    a fixture. create product in testdb and verify the result in testdb
    """
    # create table
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # clear all table after test
        Base.metadata.drop_all(bind=engine)
