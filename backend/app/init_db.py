"""Database initialization and seeding script."""
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models import CommodityGroup


COMMODITY_GROUPS = [
    (1, "General Services", "Accommodation Rentals"),
    (2, "General Services", "Membership Fees"),
    (3, "General Services", "Workplace Safety"),
    (4, "General Services", "Consulting"),
    (5, "General Services", "Financial Services"),
    (6, "General Services", "Fleet Management"),
    (7, "General Services", "Recruitment Services"),
    (8, "General Services", "Professional Development"),
    (9, "General Services", "Miscellaneous Services"),
    (10, "General Services", "Insurance"),
    (11, "Facility Management", "Electrical Engineering"),
    (12, "Facility Management", "Facility Management Services"),
    (13, "Facility Management", "Security"),
    (14, "Facility Management", "Renovations"),
    (15, "Facility Management", "Office Equipment"),
    (16, "Facility Management", "Energy Management"),
    (17, "Facility Management", "Maintenance"),
    (18, "Facility Management", "Cafeteria and Kitchenettes"),
    (19, "Facility Management", "Cleaning"),
    (20, "Publishing Production", "Audio and Visual Production"),
    (21, "Publishing Production", "Books/Videos/CDs"),
    (22, "Publishing Production", "Printing Costs"),
    (23, "Publishing Production", "Software Development for Publishing"),
    (24, "Publishing Production", "Material Costs"),
    (25, "Publishing Production", "Shipping for Production"),
    (26, "Publishing Production", "Digital Product Development"),
    (27, "Publishing Production", "Pre-production"),
    (28, "Publishing Production", "Post-production Costs"),
    (29, "Information Technology", "Hardware"),
    (30, "Information Technology", "IT Services"),
    (31, "Information Technology", "Software"),
    (32, "Logistics", "Courier, Express, and Postal Services"),
    (33, "Logistics", "Warehousing and Material Handling"),
    (34, "Logistics", "Transportation Logistics"),
    (35, "Logistics", "Delivery Services"),
    (36, "Marketing & Advertising", "Advertising"),
    (37, "Marketing & Advertising", "Outdoor Advertising"),
    (38, "Marketing & Advertising", "Marketing Agencies"),
    (39, "Marketing & Advertising", "Direct Mail"),
    (40, "Marketing & Advertising", "Customer Communication"),
    (41, "Marketing & Advertising", "Online Marketing"),
    (42, "Marketing & Advertising", "Events"),
    (43, "Marketing & Advertising", "Promotional Materials"),
    (44, "Production", "Warehouse and Operational Equipment"),
    (45, "Production", "Production Machinery"),
    (46, "Production", "Spare Parts"),
    (47, "Production", "Internal Transportation"),
    (48, "Production", "Production Materials"),
    (49, "Production", "Consumables"),
    (50, "Production", "Maintenance and Repairs"),
]


def seed_commodity_groups(db: Session) -> None:
    """
    Seed the database with commodity groups.

    Args:
        db: Database session
    """
    # Check if commodity groups already exist
    existing_count = db.query(CommodityGroup).count()
    if existing_count > 0:
        print(f"Commodity groups already seeded ({existing_count} groups found). Skipping.")
        return

    # Insert all commodity groups
    for group_id, category, name in COMMODITY_GROUPS:
        commodity_group = CommodityGroup(
            id=group_id,
            category=category,
            name=name
        )
        db.add(commodity_group)

    db.commit()
    print(f"Successfully seeded {len(COMMODITY_GROUPS)} commodity groups.")


def initialize_database() -> None:
    """
    Initialize database tables and seed data.
    This function should be called on application startup.
    """
    # Create all tables
    init_db()
    print("Database tables created.")

    # Seed commodity groups
    db = SessionLocal()
    try:
        seed_commodity_groups(db)
    finally:
        db.close()


if __name__ == "__main__":
    # Run this script directly to initialize the database
    initialize_database()
    print("Database initialization complete!")
