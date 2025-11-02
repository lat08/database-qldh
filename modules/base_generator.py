from .spec_parser import SpecParser
from .media_scanner import MediaScanner
import uuid
import os
import hmac
import hashlib
import base64
from datetime import datetime, date
from .config import *

class SQLDataGenerator:
    def __init__(self, spec_file, media_base_path):
        self.spec_file = spec_file
        self.spec_data = SpecParser(spec_file).parse()
        self.sql_statements = []
        
        # Initialize media scanner
        self.media_scanner = MediaScanner(media_base_path)
        
        self.data = {
            'persons': [],
            'user_accounts': [],
            'permissions': [],
            'instructors': [],
            'admins': [],
            'faculties': [],
            'departments': [],
            'academic_years': [],
            'semesters': [],
            'classes': [],
            'subjects': [],
            'students': [],
            'courses': [],
            'buildings': [],
            'rooms': [],
            'amenities': [],
            'course_classes': [],
            'fixed_accounts': {},
            'regulations': [],
            'training_systems': [],
            'curricula': [],
            'curriculum_details': [],
        }
        
        # Parse spec config
        self.test_config = self.spec_data.get('test_accounts_config', {})
        self.course_config = self.spec_data.get('courses_config', {})
        self.enrollment_config = self.spec_data.get('enrollment_config', {})
        self.staff_config = self.spec_data.get('staff_config', {})
        self.students_config = self.spec_data.get('students_config', {})
        self.output_config = self.spec_data.get('output_config', {})
        self.names_config = self.spec_data.get('names_config', {})

    def generate_uuid(self):
        return str(uuid.uuid4()).upper()
    
    def format_value(self, value):
        if value is None:
            return 'NULL'
        elif isinstance(value, str):
            return f"N'{value.replace("'", "''")}'"
        elif isinstance(value, (date, datetime)):
            return f"'{value.strftime('%Y-%m-%d')}'"
        elif isinstance(value, bool):
            return '1' if value else '0'
        else:
            return str(value)
    
    def bulk_insert(self, table, columns, rows):
        if not rows:
            return
        
        cols = ', '.join(columns)
        chunk_size = 1000
        
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i + chunk_size]
            values_list = []
            
            for row in chunk:
                vals = ', '.join([self.format_value(v) for v in row])
                values_list.append(f"    ({vals})")
            
            values_str = ',\n'.join(values_list)
            statement = f"INSERT INTO {table} ({cols}) VALUES\n{values_str};"
            self.sql_statements.append(statement)
    
    def add_statement(self, statement):
        self.sql_statements.append(statement)
    
    def create_password_hash(self, password, salt_bytes):
        h = hmac.new(salt_bytes, password.encode('utf-8'), hashlib.sha512)
        return base64.b64encode(h.digest()).decode('utf-8')

    def generate_all(self):
        """
        MAIN GENERATION FUNCTION
        Calls all generation methods in correct dependency order
        Methods are attached by importing modules
        """
        print("Generating SQL data from spec file...")
        
        self.add_statement("-- ============================================================")
        self.add_statement("-- EDUMANAGEMENT DATABASE - COMPLETE SCHEMA GENERATION")
        self.add_statement(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_statement(f"-- Spec file: {self.spec_file}")
        self.add_statement("-- ============================================================")
        self.add_statement("USE EduManagement;")
        self.add_statement("GO\n")
        
        # =========================================================================
        # PHASE 1: ROLES & PERMISSIONS
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 1: ROLES & PERMISSIONS")
        self.add_statement("-- =========================================================================")
        
        self.create_roles_and_permissions()
        
        # =========================================================================
        # PHASE 2: ORGANIZATIONAL STRUCTURE (MOVED UP - MUST CREATE BEFORE STAFF)
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 2: ORGANIZATIONAL STRUCTURE")
        self.add_statement("-- =========================================================================")
        
        self.create_training_systems()
        self.create_faculties_and_departments()
        self.create_academic_years_and_semesters()
        
        # =========================================================================
        # PHASE 3: PEOPLE & ACCOUNTS (MOVED DOWN - AFTER FACULTIES EXIST)
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 3: PEOPLE & ACCOUNTS")
        self.add_statement("-- =========================================================================")
        
        self.create_fixed_test_accounts()
        self.create_regular_staff()
        self.assign_faculty_deans()
        
        # =========================================================================
        # PHASE 4: PHYSICAL INFRASTRUCTURE
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 4: PHYSICAL INFRASTRUCTURE")
        self.add_statement("-- =========================================================================")
        
        self.create_buildings_and_rooms()
        self.create_room_amenities()
        self.create_room_amenity_mappings()
        
        # =========================================================================
        # PHASE 5: ACADEMIC PROGRAMS
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 5: ACADEMIC PROGRAMS")
        self.add_statement("-- =========================================================================")
        
        self.create_subjects()  # Must come first
        self.create_curricula()  # NEW: Create curricula after subjects exist
        self.create_curriculum_details()  # NEW: Map subjects to curricula
        self.create_classes()  # Now classes can reference curricula
        self.create_students()

        # =========================================================================
        # PHASE 6: COURSE OFFERINGS
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 6: COURSE OFFERINGS")
        self.add_statement("-- =========================================================================")
        
        self.create_courses()
        self.create_course_classes()
        self.create_student_enrollments()
        self.create_documents()
        
        # =========================================================================
        # PHASE 7: ASSESSMENTS
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 7: ASSESSMENTS")
        self.add_statement("-- =========================================================================")
        
        self.create_exams_and_exam_entries()
        
        # =========================================================================
        # PHASE 8: FINANCIAL & SUPPORT SERVICES
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 8: FINANCIAL & SUPPORT SERVICES")
        self.add_statement("-- =========================================================================")
        
        self.create_student_health_insurance()
        self.create_payments()
        
        # =========================================================================
        # PHASE 9: OPERATIONAL MANAGEMENT
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 9: OPERATIONAL MANAGEMENT")
        self.add_statement("-- =========================================================================")
        
        self.create_schedule_changes()
        self.create_notifications()
        self.create_notes()
        
        # =========================================================================
        # PHASE 10: REGULATIONS & POLICIES
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 10: REGULATIONS & POLICIES")
        self.add_statement("-- =========================================================================")
        
        self.create_regulations()
        
        # =========================================================================
        # FINAL STATISTICS
        # =========================================================================
        self.add_statement("\n-- ============================================================")
        self.add_statement("-- GENERATION COMPLETE - FINAL STATISTICS")
        self.add_statement("-- ============================================================")
        self.add_statement(f"-- Students: {len(self.data['students'])}")
        self.add_statement(f"-- Instructors: {len(self.data['instructors'])}")
        self.add_statement(f"-- Admins: {len(self.data['admins'])}")
        self.add_statement(f"-- Courses: {len(self.data['courses'])}")
        self.add_statement(f"-- Course Classes: {len(self.data['course_classes'])}")
        self.add_statement("-- ============================================================")
        
        return '\n'.join(self.sql_statements)

    def save_to_file(self):
        """
        Save generated SQL statements to output file
        """
        output_file = OUTPUT_FILE
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate all SQL
        sql_content = self.generate_all()
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        
        print(f"\n✓ SQL data generated successfully!")
        print(f"✓ Output file: {output_file}")
        print(f"✓ File size: {os.path.getsize(output_file) / 1024:.2f} KB")
        print(f"✓ Total SQL statements: {len(self.sql_statements)}")
        
        return output_file