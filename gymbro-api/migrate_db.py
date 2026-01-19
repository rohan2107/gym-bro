"""
Database migration script for initial table creation on PostgreSQL.

Run this ONCE after setting up Neon PostgreSQL:
    python migrate_db.py

This will create all tables in your production database.
"""
import os
from sqlmodel import SQLModel, create_engine
from app.models import User, FoodLog, Workout, ExerciseSet, WeightEntry, DailyCheckIn

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set")
    print("\nSet it first:")
    print('  $env:DATABASE_URL = "postgresql://user:pass@host/db"')
    print("  python migrate_db.py")
    exit(1)

if "sqlite" in DATABASE_URL.lower():
    print("⚠️  WARNING: You're using SQLite. This script is for PostgreSQL migration.")
    print("   For production, use a Neon PostgreSQL connection string.")
    response = input("\nContinue anyway? (y/n): ")
    if response.lower() != 'y':
        exit(0)

print(f"🔗 Connecting to database...")
print(f"   {DATABASE_URL[:30]}...")

try:
    engine = create_engine(DATABASE_URL, echo=True)
    
    print("\n📋 Creating tables...")
    SQLModel.metadata.create_all(engine)
    
    print("\n✅ Success! Database tables created:")
    print("   - users")
    print("   - food_logs")
    print("   - workouts")
    print("   - exercise_sets")
    print("   - weight_entries")
    print("   - daily_check_ins")
    print("\n🚀 Your database is ready for Vercel deployment!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("  1. Check your DATABASE_URL is correct")
    print("  2. Ensure your IP is allowed in Neon dashboard")
    print("  3. Verify the database exists")
    exit(1)
