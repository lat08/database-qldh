"""
Main orchestrator - only imports and function calls
NO function definitions here
"""

import os
import sys

# Import configuration
from modules.config import SPEC_FILE, OUTPUT_FILE, MEDIA_BASE_PATH

# Import classes
from modules.media_scanner import MediaScanner
from modules.spec_parser import SpecParser
from modules.base_generator import SQLDataGenerator

# Import function modules (they will attach to SQLDataGenerator)
from modules import roles_permissions
from modules import people_accounts
from modules import organization
from modules import infrastructure
from modules import academic
from modules import courses
from modules import enrollments
from modules import assessments
from modules import financial
from modules import operational

def main():
    # Use command line arg or default
    spec_file = sys.argv[1] if len(sys.argv) > 1 else SPEC_FILE
    
    if not os.path.exists(spec_file):
        print(f"Error: Spec file not found: {spec_file}")
        sys.exit(1)
    
    print("="*70)
    print("EDUMANAGEMENT SQL DATA GENERATOR")
    print("="*70)
    print(f"Using spec file: {spec_file}")
    print("="*70)
    
    # Make media path absolute relative to THIS file (generate_data.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    media_path = os.path.join(script_dir, MEDIA_BASE_PATH)
    
    # Create generator
    generator = SQLDataGenerator(spec_file, media_path)
    
    # Generate all data
    generator.save_to_file()
    
    print("\n" + "="*70)
    print("READY TO EXECUTE!")
    print("="*70)

if __name__ == "__main__":
    main()