from .spec_parser import SpecParser
from .media_scanner import MediaScanner
import uuid
import os
import hmac
import hashlib
import base64
from datetime import datetime, date
from .config import *

def generate_theme_insert_from_file(file_path):
    """
    Reads a theme configuration text file and generates SQL INSERT statement.
    
    Args:
        file_path: Path to the text file with theme data
        
    Returns:
        str: SQL INSERT statement
    """
    # Step 1: Read and parse the file
    data = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
    
    # Step 2: Extract values
    theme_config_id = data.get('theme_config_id', '')
    theme_name = data.get('theme_name', '')
    description = data.get('description', '')
    created_by_admin_id = data.get('created_by_admin_id', '')
    scope_type = data.get('scope_type', '')
    scope_target = data.get('scope_target', '')
    theme_variables = data.get('theme_variables', '{}')
    created_at = data.get('created_at', '')
    updated_at = data.get('updated_at', '')
    created_by = data.get('created_by', '')
    updated_by = data.get('updated_by', '')
    is_deleted = data.get('is_deleted', '0')
    is_active = data.get('is_active', '1')
    
    # Step 3: Format for SQL
    def sql_format(value, empty_as_null=False):
        if not value or value == '':
            return 'NULL' if empty_as_null else "''"
        return f"N'{value.replace("'", "''")}'"
    
    # Step 4: Build SQL INSERT
    sql = f"""INSERT INTO dbo.theme_configurations (
    theme_config_id, theme_name, description, created_by_admin_id,
    scope_type, scope_target, theme_variables, created_at,
    updated_at, created_by, updated_by, is_deleted, is_active
) VALUES (
    '{theme_config_id}',
    {sql_format(theme_name)},
    {sql_format(description)},
    '{created_by_admin_id}',
    {sql_format(scope_type)},
    {sql_format(scope_target)},
    {sql_format(theme_variables)},
    '{created_at}',
    {sql_format(updated_at, empty_as_null=True)},
    {sql_format(created_by, empty_as_null=True)},
    {sql_format(updated_by, empty_as_null=True)},
    {is_deleted},
    {is_active}
);"""
    
    return sql

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
            'divisions': [],
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
        elif isinstance(value, datetime):
            return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
        elif isinstance(value, date):
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

    def cleanup_empty_course_classes(self):
        """
        Remove course classes with 0 enrollments, except for Fall 2025 (upcoming semester)
        This prevents constraint violations and improves data quality
        """
        self.add_statement("\n-- ==================== CLEANUP: EMPTY COURSE CLASSES ====================")
        self.add_statement("-- Delete course classes with 0 enrollments")
        self.add_statement("-- PRESERVE: Fall 2025 (HK1 2025-2026) - upcoming semester for registration")
        self.add_statement("-- This cleanup prevents unnecessary empty course classes while maintaining")
        self.add_statement("-- courses available for student registration in the upcoming semester")
        self.add_statement("-- FIXED: Includes exam_entry deletion to prevent constraint violations")
        
        cleanup_sql = """
-- Count course classes with 0 enrollments before cleanup
PRINT 'BEFORE CLEANUP:';
SELECT 
    'Total Course Classes' as category,
    COUNT(*) as count
FROM course_class cc
WHERE cc.is_deleted = 0 AND cc.is_active = 1;

SELECT 
    'Course Classes with 0 Enrollments' as category,
    COUNT(*) as count
FROM course_class cc
WHERE cc.is_deleted = 0 
  AND cc.is_active = 1
  AND NOT EXISTS (
      SELECT 1 
      FROM student_enrollment se
      WHERE se.course_class_id = cc.course_class_id
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
  );

-- Identify Fall 2025 semester (HK1 2025-2026)
DECLARE @Fall2025SemesterId UNIQUEIDENTIFIER;
SELECT @Fall2025SemesterId = s.semester_id
FROM semester s
INNER JOIN academic_year ay ON s.academic_year_id = ay.academic_year_id
WHERE s.semester_type = 'fall' 
  AND ay.year_name = '2025-2026';  -- Fall 2025 is in academic year 2025-2026

-- Delete course classes with 0 enrollments, EXCEPT Fall 2025
-- Step 1: Delete dependent records first to avoid constraint violations

-- Delete enrollment_grade_detail records for empty course classes (except Fall 2025)
DELETE egd
FROM enrollment_grade_detail egd
INNER JOIN enrollment_grade_version egv ON egd.grade_version_id = egv.grade_version_id
INNER JOIN course_class cc ON egv.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
WHERE cc.is_deleted = 0 
  AND cc.is_active = 1
  AND c.semester_id != @Fall2025SemesterId  -- PRESERVE Fall 2025
  AND NOT EXISTS (
      SELECT 1 
      FROM student_enrollment se
      WHERE se.course_class_id = cc.course_class_id
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
  );

-- Delete enrollment_grade_version records for empty course classes (except Fall 2025)
DELETE egv
FROM enrollment_grade_version egv
INNER JOIN course_class cc ON egv.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
WHERE cc.is_deleted = 0 
  AND cc.is_active = 1
  AND c.semester_id != @Fall2025SemesterId  -- PRESERVE Fall 2025
  AND NOT EXISTS (
      SELECT 1 
      FROM student_enrollment se
      WHERE se.course_class_id = cc.course_class_id
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
  );

-- Delete exam_entry records for empty course classes (except Fall 2025)
DELETE ee
FROM exam_entry ee
INNER JOIN course_class cc ON ee.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
WHERE cc.is_deleted = 0 
  AND cc.is_active = 1
  AND c.semester_id != @Fall2025SemesterId  -- PRESERVE Fall 2025
  AND NOT EXISTS (
      SELECT 1 
      FROM student_enrollment se
      WHERE se.course_class_id = cc.course_class_id
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
  );

-- Delete exam_class records for empty course classes (except Fall 2025)
DELETE ec
FROM exam_class ec
INNER JOIN course_class cc ON ec.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
WHERE cc.is_deleted = 0 
  AND cc.is_active = 1
  AND c.semester_id != @Fall2025SemesterId  -- PRESERVE Fall 2025
  AND NOT EXISTS (
      SELECT 1 
      FROM student_enrollment se
      WHERE se.course_class_id = cc.course_class_id
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
  );

-- Delete schedule_change records for empty course classes (except Fall 2025)
DELETE sc
FROM schedule_change sc
INNER JOIN course_class cc ON sc.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
WHERE cc.is_deleted = 0 
  AND cc.is_active = 1
  AND c.semester_id != @Fall2025SemesterId  -- PRESERVE Fall 2025
  AND NOT EXISTS (
      SELECT 1 
      FROM student_enrollment se
      WHERE se.course_class_id = cc.course_class_id
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
  );

-- Delete schedule_change_request records for empty course classes (except Fall 2025)
DELETE csr
FROM schedule_change_request csr
INNER JOIN course_class cc ON csr.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
WHERE cc.is_deleted = 0 
  AND cc.is_active = 1
  AND c.semester_id != @Fall2025SemesterId  -- PRESERVE Fall 2025
  AND NOT EXISTS (
      SELECT 1 
      FROM student_enrollment se
      WHERE se.course_class_id = cc.course_class_id
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
  );

-- Step 2: Finally, delete the empty course classes themselves (except Fall 2025)
DECLARE @DeletedCount INT;

DELETE cc
FROM course_class cc
INNER JOIN course c ON cc.course_id = c.course_id
WHERE cc.is_deleted = 0 
  AND cc.is_active = 1
  AND c.semester_id != @Fall2025SemesterId  -- PRESERVE Fall 2025
  AND NOT EXISTS (
      SELECT 1 
      FROM student_enrollment se
      WHERE se.course_class_id = cc.course_class_id
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
  );

SET @DeletedCount = @@ROWCOUNT;

-- Count remaining course classes after cleanup
PRINT '';
PRINT 'AFTER CLEANUP:';
SELECT 
    'Total Course Classes' as category,
    COUNT(*) as count
FROM course_class cc
WHERE cc.is_deleted = 0 AND cc.is_active = 1;

SELECT 
    'Course Classes with 0 Enrollments' as category,
    COUNT(*) as count
FROM course_class cc
WHERE cc.is_deleted = 0 
  AND cc.is_active = 1
  AND NOT EXISTS (
      SELECT 1 
      FROM student_enrollment se
      WHERE se.course_class_id = cc.course_class_id
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
  );

SELECT 
    'Fall 2025 Course Classes (Preserved)' as category,
    COUNT(*) as count
FROM course_class cc
INNER JOIN course c ON cc.course_id = c.course_id
WHERE cc.is_deleted = 0 
  AND cc.is_active = 1
  AND c.semester_id = @Fall2025SemesterId;

PRINT 'CLEANUP SUMMARY:';
PRINT 'Deleted ' + CAST(@DeletedCount AS NVARCHAR(10)) + ' empty course classes (excluding Fall 2025)';
PRINT 'Fall 2025 course classes preserved for upcoming registration';"""

        self.add_statement(cleanup_sql)

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
        self.add_statement("-- PHASE 10: REGULATIONS & POLICIES & THEMES")
        self.add_statement("-- =========================================================================")
        
        self.create_regulations()

        self.add_statement("\n\n-- =========================================================================\n\n")

        self.add_statement(generate_theme_insert_from_file(r'database-qldh\theme_configurations.txt'))

        self.add_statement("\n\n-- =========================================================================\n\n")
        
        # =========================================================================
        # PHASE 11: CHATBOT KNOWLEDGE BASE
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 11: CHATBOT KNOWLEDGE BASE")
        self.add_statement("-- =========================================================================")
        
        # Read and append ChatBot.sql content
        chatbot_sql_path = r'database-qldh\sql\ChatBot.sql'
        try:
            with open(chatbot_sql_path, 'r', encoding='utf-8-sig') as f:
                chatbot_content = f.read().strip()
                self.add_statement(chatbot_content)
        except FileNotFoundError:
            self.add_statement(f"-- Warning: ChatBot.sql file not found at {chatbot_sql_path}")
        except Exception as e:
            self.add_statement(f"-- Error reading ChatBot.sql: {str(e)}")
        
        self.add_statement("\n-- =========================================================================")
        
        # =========================================================================
        # PHASE 12: DATA CLEANUP - REMOVE EMPTY COURSE CLASSES
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 12: DATA CLEANUP - REMOVE EMPTY COURSE CLASSES")
        self.add_statement("-- =========================================================================")
        
        self.cleanup_empty_course_classes()
        
        # =========================================================================
        # PHASE 13: PAYMENT PROCESSING - PAY FOR PAST ENROLLMENTS
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 13: PAYMENT PROCESSING - PAY FOR PAST ENROLLMENTS")
        self.add_statement("-- =========================================================================")
        
        # Read and append pay_for_past.sql content
        pay_for_past_sql_path = r'database-qldh\sql\fix\pay_for_past.sql'
        try:
            with open(pay_for_past_sql_path, 'r', encoding='utf-8-sig') as f:
                pay_for_past_content = f.read().strip()
                self.add_statement(pay_for_past_content)
        except FileNotFoundError:
            self.add_statement(f"-- Warning: pay_for_past.sql file not found at {pay_for_past_sql_path}")
        except Exception as e:
            self.add_statement(f"-- Error reading pay_for_past.sql: {str(e)}")
        
        self.add_statement("\n-- =========================================================================")
        
        # =========================================================================
        # PHASE 14: CONFLICT RESOLUTION - DELETE CONFLICTING ENTRIES
        # =========================================================================
        self.add_statement("\n-- =========================================================================")
        self.add_statement("-- PHASE 14: CONFLICT RESOLUTION - DELETE CONFLICTING ENTRIES")
        self.add_statement("-- =========================================================================")
        
        # Read and append delete_conflicts.sql content
        delete_conflicts_sql_path = r'database-qldh\sql\fix\delete_conflicts.sql'
        try:
            with open(delete_conflicts_sql_path, 'r', encoding='utf-8-sig') as f:
                delete_conflicts_content = f.read().strip()
                self.add_statement(delete_conflicts_content)
        except FileNotFoundError:
            self.add_statement(f"-- Warning: delete_conflicts.sql file not found at {delete_conflicts_sql_path}")
        except Exception as e:
            self.add_statement(f"-- Error reading delete_conflicts.sql: {str(e)}")
        
        self.add_statement("\n-- =========================================================================")
        
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
        Appends ChatBot.sql at the end
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