"""
Property Data Source
Provides access to structured property information and maintenance records
Expands beyond just company knowledge to include property-specific data
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class PropertyDatabase:
    """
    In-memory property database for demonstration.
    Can be extended to connect to actual property management systems.
    """

    def __init__(self):
        """Initialize property database with sample data."""
        self.properties = self._init_properties()
        self.maintenance_records = self._init_maintenance()
        self.vendors = self._init_vendors()

    def _init_properties(self) -> Dict[str, Dict]:
        """Initialize sample property data."""
        return {
            "prop-001": {
                "id": "prop-001",
                "address": "999 Park Avenue, New York, NY 10021",
                "type": "penthouse",
                "owner": "Premium Tier Client",
                "square_feet": 5000,
                "bedrooms": 4,
                "bathrooms": 3,
                "features": [
                    "Smart home automation",
                    "Wine cellar",
                    "Home theater",
                    "Rooftop terrace",
                    "In-unit spa",
                ],
                "last_inspection": "2026-03-15",
                "next_maintenance": "2026-04-30",
                "insurance_provider": "Lloyd's of London",
            },
            "prop-002": {
                "id": "prop-002",
                "address": "500 Fifth Avenue, New York, NY 10110",
                "type": "townhouse",
                "owner": "Platinum Tier Client",
                "square_feet": 4200,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "features": [
                    "Private garden",
                    "Library",
                    "Gym",
                    "Elevator access",
                ],
                "last_inspection": "2026-02-28",
                "next_maintenance": "2026-05-15",
                "insurance_provider": "Chubb",
            },
            "prop-003": {
                "id": "prop-003",
                "address": "Central Park West, New York, NY 10023",
                "type": "apartment",
                "owner": "Premium Tier Client",
                "square_feet": 3500,
                "bedrooms": 3,
                "bathrooms": 2,
                "features": [
                    "Park views",
                    "High-speed internet",
                    "Climate control",
                ],
                "last_inspection": "2026-03-20",
                "next_maintenance": "2026-06-10",
                "insurance_provider": "Liberty Mutual",
            },
        }

    def _init_maintenance(self) -> List[Dict]:
        """Initialize sample maintenance records."""
        return [
            {
                "id": "maint-001",
                "property_id": "prop-001",
                "type": "HVAC System Service",
                "date": "2026-03-10",
                "status": "completed",
                "cost": 2500,
                "vendor": "Climate Tech Solutions",
                "notes": "Annual HVAC inspection and cleaning completed. System operating at optimal efficiency.",
            },
            {
                "id": "maint-002",
                "property_id": "prop-001",
                "type": "Rooftop Inspection",
                "date": "2026-03-15",
                "status": "scheduled",
                "cost": 1800,
                "vendor": "Roofing Excellence Inc.",
                "notes": "Spring inspection to check for weather damage and drainage issues.",
            },
            {
                "id": "maint-003",
                "property_id": "prop-002",
                "type": "Electrical System Upgrade",
                "date": "2026-02-15",
                "status": "completed",
                "cost": 8500,
                "vendor": "Electrical Innovations",
                "notes": "Updated electrical panel and installed backup generator.",
            },
            {
                "id": "maint-004",
                "property_id": "prop-002",
                "type": "Plumbing Maintenance",
                "date": "2026-04-05",
                "status": "scheduled",
                "cost": 3200,
                "vendor": "Premier Plumbing",
                "notes": "Water line inspection and filter replacements.",
            },
            {
                "id": "maint-005",
                "property_id": "prop-003",
                "type": "Window Cleaning",
                "date": "2026-03-25",
                "status": "completed",
                "cost": 800,
                "vendor": "Crystal Clear Windows",
                "notes": "Interior and exterior window cleaning and inspection.",
            },
        ]

    def _init_vendors(self) -> Dict[str, Dict]:
        """Initialize trusted vendor database."""
        return {
            "vendor-001": {
                "id": "vendor-001",
                "name": "Climate Tech Solutions",
                "category": "HVAC",
                "rating": 4.8,
                "background_check": True,
                "insurance": True,
                "specialties": ["HVAC maintenance", "Air quality", "Energy efficiency"],
                "phone": "+1-555-200-1001",
            },
            "vendor-002": {
                "id": "vendor-002",
                "name": "Roofing Excellence Inc.",
                "category": "Roofing",
                "rating": 4.9,
                "background_check": True,
                "insurance": True,
                "specialties": ["Roof inspection", "Repairs", "Replacement"],
                "phone": "+1-555-200-1002",
            },
            "vendor-003": {
                "id": "vendor-003",
                "name": "Electrical Innovations",
                "category": "Electrical",
                "rating": 4.7,
                "background_check": True,
                "insurance": True,
                "specialties": ["System upgrades", "Generator installation", "Smart home"],
                "phone": "+1-555-200-1003",
            },
            "vendor-004": {
                "id": "vendor-004",
                "name": "Premier Plumbing",
                "category": "Plumbing",
                "rating": 4.6,
                "background_check": True,
                "insurance": True,
                "specialties": ["Maintenance", "Repairs", "Water systems"],
                "phone": "+1-555-200-1004",
            },
            "vendor-005": {
                "id": "vendor-005",
                "name": "Crystal Clear Windows",
                "category": "Cleaning & Maintenance",
                "rating": 4.8,
                "background_check": True,
                "insurance": True,
                "specialties": ["Window cleaning", "Pressure washing", "Inspections"],
                "phone": "+1-555-200-1005",
            },
        }

    def search_properties(self, query: str) -> List[Dict]:
        """
        Search properties by address or attributes.

        Args:
            query: Search term

        Returns:
            List of matching properties
        """
        query_lower = query.lower()
        results = []
        
        for prop in self.properties.values():
            if (query_lower in prop["address"].lower() or
                query_lower in prop["type"].lower()):
                results.append(prop)
        
        return results

    def get_property(self, property_id: str) -> Optional[Dict]:
        """Get property details by ID."""
        return self.properties.get(property_id)

    def get_all_properties(self) -> List[Dict]:
        """Get all properties."""
        return list(self.properties.values())

    def get_maintenance_history(self, property_id: str, limit: int = 10) -> List[Dict]:
        """Get maintenance records for a property."""
        records = [
            m for m in self.maintenance_records
            if m["property_id"] == property_id
        ]
        return records[:limit]

    def get_scheduled_maintenance(self, property_id: str) -> List[Dict]:
        """Get upcoming maintenance for a property."""
        return [
            m for m in self.maintenance_records
            if m["property_id"] == property_id and m["status"] == "scheduled"
        ]

    def add_maintenance_record(
        self,
        property_id: str,
        maintenance_type: str,
        date: str,
        vendor_id: str,
        cost: float,
        notes: str = "",
    ) -> Dict:
        """Schedule new maintenance for a property."""
        record_id = f"maint-{len(self.maintenance_records) + 1:03d}"
        
        record = {
            "id": record_id,
            "property_id": property_id,
            "type": maintenance_type,
            "date": date,
            "status": "scheduled",
            "cost": cost,
            "vendor": self.vendors.get(vendor_id, {}).get("name", "To be assigned"),
            "notes": notes,
        }
        
        self.maintenance_records.append(record)
        logger.info(f"Added maintenance record {record_id} for property {property_id}")
        return record

    def search_vendors(self, category: str) -> List[Dict]:
        """Search vendors by category."""
        results = []
        category_lower = category.lower()
        
        for vendor in self.vendors.values():
            if category_lower in vendor["category"].lower():
                results.append(vendor)
        
        return results

    def get_vendor(self, vendor_id: str) -> Optional[Dict]:
        """Get vendor details by ID."""
        return self.vendors.get(vendor_id)

    def get_all_vendors(self) -> List[Dict]:
        """Get all vendors."""
        return list(self.vendors.values())

    def format_property_for_llm(self, property_id: str) -> str:
        """Format property information for LLM context."""
        prop = self.get_property(property_id)
        if not prop:
            return ""
        
        maintenance = self.get_maintenance_history(property_id, limit=5)
        
        formatted = f"""
**Property: {prop['address']}**
- Type: {prop['type'].title()}
- Size: {prop['square_feet']:,} sq ft
- Bedrooms: {prop['bedrooms']} | Bathrooms: {prop['bathrooms']}
- Features: {', '.join(prop['features'])}
- Last Inspection: {prop['last_inspection']}
- Next Maintenance: {prop['next_maintenance']}

**Recent Maintenance:**
"""
        for record in maintenance:
            formatted += f"\n- {record['date']}: {record['type']} ({record['status']}) - {record['vendor']}"
        
        return formatted

    def format_vendor_for_llm(self, vendor_id: str) -> str:
        """Format vendor information for LLM context."""
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return ""
        
        return f"""
**Vendor: {vendor['name']}**
- Category: {vendor['category']}
- Rating: {vendor['rating']}/5.0
- Background Check: {'✓' if vendor['background_check'] else '✗'}
- Insurance: {'✓' if vendor['insurance'] else '✗'}
- Specialties: {', '.join(vendor['specialties'])}
- Phone: {vendor['phone']}
"""
