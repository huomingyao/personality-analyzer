"""Test script for web_api services."""

import sys
import os

# Fix path
PROJECT_DIR = r"D:\person_fenxi"
SRC_DIR = os.path.join(PROJECT_DIR, "src")

for p in [SRC_DIR, PROJECT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

print("Testing AnalyzeService...")
from src.services.analyze_service import AnalyzeService

service = AnalyzeService()
print("  Created OK")

skills = service.get_available_skills()
print(f"  Available skills: {len(skills)}")
for s in skills:
    print(f"    - {s['display_name']}")

print("\n✅ All tests passed!")