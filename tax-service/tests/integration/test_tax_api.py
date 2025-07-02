import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app
from app.models.tax_model import TaxRate

# Create test database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/test_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def test_db():
    # Create the test database tables
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    db = TestingSessionLocal()
    db.add(TaxRate(country="US", state="CA", rate=0.0925))
    db.add(TaxRate(country="US", state="NY", rate=0.0845))
    db.add(TaxRate(country="US", state="TX", rate=0.0625))
    db.commit()
    
    # Override the get_db dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c

def test_calculate_tax(client):
    """Test the calculate tax endpoint"""
    # Arrange
    payload = {
        "amount": 100.0,
        "country": "US",
        "state": "CA"
    }
    
    # Act
    response = client.post("/api/tax/calculate", json=payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "tax_amount" in data
    assert data["tax_amount"] == 9.25

def test_get_tax_rates(client):
    """Test getting all tax rates"""
    # Act
    response = client.get("/api/tax/rates")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert any(rate["country"] == "US" and rate["state"] == "CA" and rate["rate"] == 0.0925 for rate in data)
    assert any(rate["country"] == "US" and rate["state"] == "NY" and rate["rate"] == 0.0845 for rate in data)
    assert any(rate["country"] == "US" and rate["state"] == "TX" and rate["rate"] == 0.0625 for rate in data)

def test_get_tax_rate_by_location(client):
    """Test getting tax rate by location"""
    # Act
    response = client.get("/api/tax/rates/US/CA")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["country"] == "US"
    assert data["state"] == "CA"
    assert data["rate"] == 0.0925

def test_get_tax_rate_not_found(client):
    """Test getting tax rate for location that doesn't exist"""
    # Act
    response = client.get("/api/tax/rates/US/FL")
    
    # Assert
    assert response.status_code == 404
