"""Unit tests for property database."""

import pytest
from chatbot.property_database import PropertyDatabase


class TestPropertyDatabase:
    """Test suite for PropertyDatabase."""

    @pytest.mark.unit
    def test_initialization(self, property_db):
        """Test property database initialization."""
        assert property_db is not None
        assert len(property_db.properties) > 0
        assert len(property_db.vendors) > 0
        assert len(property_db.maintenance_records) > 0

    @pytest.mark.unit
    def test_get_all_properties(self, property_db):
        """Test getting all properties."""
        properties = property_db.get_all_properties()
        
        assert len(properties) >= 3
        assert any(p["id"] == "prop-001" for p in properties)

    @pytest.mark.unit
    def test_get_property(self, property_db):
        """Test getting a specific property."""
        prop = property_db.get_property("prop-001")
        
        assert prop is not None
        assert prop["id"] == "prop-001"
        assert prop["address"] == "999 Park Avenue, New York, NY 10021"

    @pytest.mark.unit
    def test_get_nonexistent_property(self, property_db):
        """Test getting a non-existent property."""
        prop = property_db.get_property("nonexistent")
        assert prop is None

    @pytest.mark.unit
    def test_search_properties_by_address(self, property_db):
        """Test searching properties by address."""
        results = property_db.search_properties("Park Avenue")
        
        assert len(results) > 0
        assert any("Park Avenue" in p["address"] for p in results)

    @pytest.mark.unit
    def test_search_properties_by_type(self, property_db):
        """Test searching properties by type."""
        results = property_db.search_properties("penthouse")
        
        assert len(results) > 0
        assert any(p["type"] == "penthouse" for p in results)

    @pytest.mark.unit
    def test_search_properties_no_results(self, property_db):
        """Test searching properties with no results."""
        results = property_db.search_properties("nonexistent location")
        assert len(results) == 0

    @pytest.mark.unit
    def test_get_maintenance_history(self, property_db):
        """Test getting maintenance history for a property."""
        records = property_db.get_maintenance_history("prop-001")
        
        assert len(records) > 0
        assert all(r["property_id"] == "prop-001" for r in records)

    @pytest.mark.unit
    def test_get_scheduled_maintenance(self, property_db):
        """Test getting scheduled maintenance."""
        scheduled = property_db.get_scheduled_maintenance("prop-001")
        
        assert len(scheduled) > 0
        assert all(m["status"] == "scheduled" for m in scheduled)

    @pytest.mark.unit
    def test_get_completed_maintenance_not_returned(self, property_db):
        """Test that completed maintenance is not in scheduled."""
        scheduled = property_db.get_scheduled_maintenance("prop-001")
        
        assert all(m["status"] != "completed" for m in scheduled)

    @pytest.mark.unit
    def test_add_maintenance_record(self, property_db):
        """Test adding a new maintenance record."""
        record = property_db.add_maintenance_record(
            "prop-001",
            "Pool Cleaning",
            "2026-04-15",
            "vendor-001",
            cost=500,
            notes="Spring pool maintenance"
        )
        
        assert record is not None
        assert record["type"] == "Pool Cleaning"
        assert record["status"] == "scheduled"
        assert record["cost"] == 500

    @pytest.mark.unit
    def test_added_record_in_history(self, property_db):
        """Test that added maintenance appears in history."""
        initial_count = len(property_db.get_maintenance_history("prop-002"))
        
        property_db.add_maintenance_record(
            "prop-002",
            "Test Maintenance",
            "2026-04-20",
            "vendor-002"
        )
        
        new_count = len(property_db.get_maintenance_history("prop-002"))
        assert new_count == initial_count + 1

    @pytest.mark.unit
    def test_get_all_vendors(self, property_db):
        """Test getting all vendors."""
        vendors = property_db.get_all_vendors()
        
        assert len(vendors) >= 5
        assert any(v["id"] == "vendor-001" for v in vendors)

    @pytest.mark.unit
    def test_get_vendor(self, property_db):
        """Test getting a specific vendor."""
        vendor = property_db.get_vendor("vendor-001")
        
        assert vendor is not None
        assert vendor["name"] == "Climate Tech Solutions"
        assert vendor["category"] == "HVAC"

    @pytest.mark.unit
    def test_get_nonexistent_vendor(self, property_db):
        """Test getting a non-existent vendor."""
        vendor = property_db.get_vendor("nonexistent")
        assert vendor is None

    @pytest.mark.unit
    def test_search_vendors_by_category(self, property_db):
        """Test searching vendors by category."""
        results = property_db.search_vendors("HVAC")
        
        assert len(results) > 0
        assert any("HVAC" in v["category"] for v in results)

    @pytest.mark.unit
    def test_search_vendors_no_results(self, property_db):
        """Test searching vendors with no results."""
        results = property_db.search_vendors("NonExistent")
        assert len(results) == 0

    @pytest.mark.unit
    def test_vendor_attributes(self, property_db):
        """Test vendor has required attributes."""
        vendor = property_db.get_vendor("vendor-001")
        
        assert "name" in vendor
        assert "category" in vendor
        assert "rating" in vendor
        assert "background_check" in vendor
        assert "insurance" in vendor
        assert "specialties" in vendor
        assert "phone" in vendor

    @pytest.mark.unit
    def test_format_property_for_llm(self, property_db):
        """Test formatting property information for LLM."""
        formatted = property_db.format_property_for_llm("prop-001")
        
        assert "Park Avenue" in formatted
        assert "penthouse" in formatted or "5000" in formatted

    @pytest.mark.unit
    def test_format_vendor_for_llm(self, property_db):
        """Test formatting vendor information for LLM."""
        formatted = property_db.format_vendor_for_llm("vendor-001")
        
        assert "Climate Tech Solutions" in formatted
        assert "HVAC" in formatted

    @pytest.mark.unit
    def test_property_has_required_fields(self, property_db):
        """Test that properties have required fields."""
        prop = property_db.get_property("prop-001")
        
        required_fields = ["id", "address", "type", "square_feet", 
                          "bedrooms", "bathrooms", "features"]
        for field in required_fields:
            assert field in prop, f"Missing field: {field}"

    @pytest.mark.unit
    def test_maintenance_has_required_fields(self, property_db):
        """Test that maintenance records have required fields."""
        records = property_db.get_maintenance_history("prop-001")
        record = records[0]
        
        required_fields = ["id", "property_id", "type", "date", "status"]
        for field in required_fields:
            assert field in record, f"Missing field: {field}"
