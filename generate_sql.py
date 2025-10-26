"""
EduManagement SQL Data Generator - Spec-Driven (UPDATED SCHEMA)
===============================================
Reads configuration from spec file and generates REALISTIC, MASSIVE data
Includes proper course_class scheduling and student enrollments
UPDATED: Removed room_booking, exam_schedule now references room directly
"""

# ==================== CONFIGURATION ====================
SPEC_FILE = r'specs.txt' 
OUTPUT_FILE = r'insert_data.sql'
# ========================================================

import uuid
import random
import os
import hmac
import hashlib
import base64
from datetime import datetime, date, timedelta
from collections import defaultdict

# ==================== MEDIA CONFIGURATION ====================
SUPABASE_BASE_URL = "https://baygtczqmdoolsvkxgpr.supabase.co/storage/v1/object/public"

MEDIA_BUCKETS = {
    'profile_pics': 'profile_pics',
    'instructor_documents': 'instructor_documents/demo',
    'room_pics': 'room_pics',
    'exams': 'exams/demo',
    'regulations': 'regulations'
}

class MediaScanner:
    """Scans media folders and tracks available files"""
    def __init__(self, media_base_path='medias'):
        self.media_base_path = media_base_path
        self.files = {
            'profile_pics': [],
            'course_docs': {'pdf': [], 'images': [], 'excel': []},
            'room_pics': [],
            'regulations': []
        }
        self.scan_files()
    
    def scan_files(self):
        """Scan all media folders and categorize files"""
        # Profile pictures
        profile_path = os.path.join(self.media_base_path, 'profile_pics')
        if os.path.exists(profile_path):
            self.files['profile_pics'] = [
                f for f in os.listdir(profile_path) 
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))
            ]
        
        # Course documents
        course_docs_path = os.path.join(self.media_base_path, 'course_docs')
        if os.path.exists(course_docs_path):
            for file in os.listdir(course_docs_path):
                file_lower = file.lower()
                if file_lower.endswith('.pdf'):
                    self.files['course_docs']['pdf'].append(file)
                elif file_lower.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    self.files['course_docs']['images'].append(file)
                elif file_lower.endswith(('.xls', '.xlsx', '.xlsm')):
                    self.files['course_docs']['excel'].append(file)
        
        # Room pictures
        room_pics_path = os.path.join(self.media_base_path, 'room_pics')
        if os.path.exists(room_pics_path):
            self.files['room_pics'] = [
                f for f in os.listdir(room_pics_path)
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))
            ]
        
        # Regulations (if stored locally)
        regulations_path = os.path.join(self.media_base_path, 'regulations')
        if os.path.exists(regulations_path):
            self.files['regulations'] = [
                f for f in os.listdir(regulations_path)
                if f.lower().endswith('.pdf')
            ]
    
    def get_random_file(self, category, subcategory=None):
        """Get a random file from a category"""
        if subcategory:
            files = self.files.get(category, {}).get(subcategory, [])
        else:
            files = self.files.get(category, [])
        
        if files:
            return random.choice(files)
        return None
    
    def build_url(self, bucket_key, filename):
        """Build Supabase storage URL"""
        bucket_path = MEDIA_BUCKETS.get(bucket_key)
        if not bucket_path:
            return None
        return f"{SUPABASE_BASE_URL}/{bucket_path}/{filename}"

class SpecParser:
    def __init__(self, spec_file):
        self.spec_file = spec_file
        self.data = {}
        self.current_section = None
        
    def parse(self):
        with open(self.spec_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('[') and line.endswith(']'):
                    self.current_section = line[1:-1]
                    self.data[self.current_section] = []
                # IMPORTANT: Check for pipe FIRST (before colon)
                # This prevents URLs with colons from being parsed as config
                elif self.current_section and '|' in line:
                    self.data[self.current_section].append(line)
                # Then check for colon (for config lines)
                elif self.current_section and ':' in line:
                    # Make sure it's a config line (key: value format)
                    if line.count(':') >= 1 and not line.startswith('http'):
                        key, value = line.split(':', 1)
                        self.data.setdefault(self.current_section + '_config', {})[key.strip()] = value.strip()
        
        return self.data
    
class SQLDataGenerator:
    def __init__(self, spec_file):
        self.spec_file = spec_file
        self.spec_data = SpecParser(spec_file).parse()
        self.sql_statements = []
        
        # Initialize media scanner
        self.media_scanner = MediaScanner()
        
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
            'regulations': []
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

    def create_regulations(self):
        """
        Generate regulation records from spec file
        """
        self.add_statement("\n-- ==================== REGULATIONS ====================")
        
        regulation_rows = []
        
        # Get admin for created_by - using simple ID
        admin_id = self.data['fixed_accounts']['admin']['admin_id']
        
        self.add_statement(f"-- Using admin_id: {admin_id}")
        self.add_statement(f"-- Found {len(self.spec_data.get('regulations', []))} regulation entries in spec")
        
        for line in self.spec_data.get('regulations', []):
            parts = [p.strip() for p in line.split('|')]
            
            if len(parts) < 4:
                self.add_statement(f"-- WARNING: Invalid regulation line (need at least 4 parts): {line[:100]}...")
                continue
            
            regulation_name = parts[0]
            target = parts[1]
            pdf_path = parts[2]
            description = parts[3]
            expire_date = None
            
            # Handle expire_date (5th part is optional)
            if len(parts) > 4:
                expire_val = parts[4].strip()
                if expire_val and expire_val.upper() != 'NULL':
                    try:
                        expire_date = datetime.strptime(expire_val, '%Y-%m-%d').date()
                    except:
                        expire_date = None
            
            # Validate target
            if target not in ['student', 'instructor']:
                self.add_statement(f"-- WARNING: Invalid target '{target}' for regulation: {regulation_name}")
                continue
            
            regulation_id = self.generate_uuid()
            
            self.data['regulations'].append({
                'regulation_id': regulation_id,
                'regulation_name': regulation_name,
                'target': target
            })
            
            regulation_rows.append([
                regulation_id,
                regulation_name,
                target,
                pdf_path,
                description,
                expire_date,
                admin_id  # Using simple predictable admin_id
            ])
            
            self.add_statement(f"-- Added: {regulation_name} (target: {target})")
        
        self.add_statement(f"-- Total regulations to insert: {len(regulation_rows)}")
        
        if len(regulation_rows) > 0:
            self.bulk_insert('regulation',
                            ['regulation_id', 'regulation_name', 'target', 'pdf_file_path', 
                            'regulation_description', 'expire_date', 'created_by_admin'],
                            regulation_rows)
        else:
            self.add_statement("-- WARNING: No regulations to insert!")

    # ==================== PERMISSIONS ====================
    def create_permissions(self):
        self.add_statement("\n-- ==================== PERMISSIONS ====================")
        
        permissions_data = [
            ('Admin', 'admin_manage_users', 'Quản lý người dùng'),
            ('Admin', 'admin_manage_courses', 'Quản lý khóa học'),
            ('Admin', 'admin_manage_rooms', 'Quản lý phòng học'),
            ('Admin', 'admin_manage_students', 'Quản lý sinh viên'),
            ('Admin', 'admin_manage_instructors', 'Quản lý giảng viên'),
            ('Admin', 'admin_view_all_grades', 'Xem tất cả điểm'),
            ('Instructor', 'instructor_view_schedule', 'Xem lịch giảng dạy'),
            ('Instructor', 'instructor_edit_grades', 'Chỉnh sửa điểm'),
            ('Instructor', 'instructor_view_student_list', 'Xem danh sách sinh viên'),
            ('Instructor', 'instructor_upload_materials', 'Upload tài liệu'),
            ('Student', 'student_view_schedule', 'Xem lịch học'),
            ('Student', 'student_view_grades', 'Xem điểm'),
            ('Student', 'student_register_courses', 'Đăng ký học phần'),
            ('Student', 'student_view_materials', 'Xem tài liệu học tập'),
        ]
        
        rows = []
        for role_name, perm_name, desc in permissions_data:
            perm_id = self.generate_uuid()
            self.data['permissions'].append({'permission_id': perm_id, 'role_name': role_name})
            rows.append([perm_id, role_name, perm_name, desc])
        
        self.bulk_insert('permission', ['permission_id', 'role_name', 'permission_name', 'description'], rows)
    
    def create_fixed_test_accounts(self):
        self.add_statement("\n-- ==================== FIXED TEST ACCOUNTS ====================")
        
        password = self.test_config.get('password', '123456')
        salt_b64 = self.test_config.get('salt_base64', 'MTExMQ==')
        salt_bytes = base64.b64decode(salt_b64)
        password_hash = self.create_password_hash(password, salt_bytes)
        
        self.add_statement(f"-- Password: {password}")
        self.add_statement(f"-- Salt: {salt_b64}")
        self.add_statement(f"-- Hash: {password_hash}")
        self.add_statement("-- Using SIMPLE PREDICTABLE IDs for easy testing")
        
        person_rows = []
        user_rows = []
        instructor_rows = []
        admin_rows = []
        
        # ============================================================
        # INSTRUCTOR - Simple IDs
        # ============================================================
        person_id = self.test_config.get('instructor_person_id', '00000000-0000-0000-0000-000000000011')
        user_id = self.test_config.get('instructor_user_id', '00000000-0000-0000-0000-000000000012')
        instructor_id = self.test_config.get('instructor_id', '00000000-0000-0000-0000-000000000013')
        
        self.data['fixed_accounts']['instructor'] = {
            'person_id': person_id,
            'user_id': user_id,
            'instructor_id': instructor_id,
            'full_name': self.test_config.get('instructor_name', 'Test Instructor')
        }
        
        instructor_citizen_id = f"{random.randint(100000000000, 999999999999)}"
        
        # Get random profile picture
        profile_pic = self.media_scanner.get_random_file('profile_pics')
        profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
        
        person_rows.append([person_id, self.test_config.get('instructor_name'), 
                        self.test_config.get('instructor_dob', '1985-01-01'),
                        self.test_config.get('instructor_gender', 'female'),
                        self.test_config.get('instructor_email'),
                        self.test_config.get('instructor_phone'),
                        instructor_citizen_id,
                        'TP Hồ Chí Minh',
                        profile_pic_url])
        
        user_rows.append([user_id, person_id, self.test_config.get('instructor_username'),
                        password_hash, salt_b64, 'Instructor', 'active'])
        
        instructor_rows.append([instructor_id, person_id, self.test_config.get('instructor_code'),
                            self.test_config.get('instructor_degree'), 
                            self.test_config.get('instructor_specialization', 'Công nghệ thông tin'),
                            None,  # department_id
                            self.test_config.get('instructor_hire_date'), 'active'])
        
        self.data['instructors'].append({'instructor_id': instructor_id, 'person_id': person_id,
                                        'full_name': self.test_config.get('instructor_name')})
        
        self.add_statement(f"-- INSTRUCTOR IDs: person={person_id}, user={user_id}, instructor={instructor_id}")
        
        # ============================================================
        # ADMIN - Simple IDs
        # ============================================================
        person_id = self.test_config.get('admin_person_id', '00000000-0000-0000-0000-000000000021')
        user_id = self.test_config.get('admin_user_id', '00000000-0000-0000-0000-000000000022')
        admin_id = self.test_config.get('admin_id', '00000000-0000-0000-0000-000000000023')
        
        self.data['fixed_accounts']['admin'] = {
            'person_id': person_id, 
            'user_id': user_id, 
            'admin_id': admin_id
        }
        
        admin_citizen_id = f"{random.randint(100000000000, 999999999999)}"
        
        # Get random profile picture
        profile_pic = self.media_scanner.get_random_file('profile_pics')
        profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
        
        person_rows.append([person_id, self.test_config.get('admin_name'),
                        self.test_config.get('admin_dob'),
                        self.test_config.get('admin_gender'),
                        self.test_config.get('admin_email'),
                        self.test_config.get('admin_phone'),
                        admin_citizen_id,
                        'TP Hồ Chí Minh',
                        profile_pic_url])
        
        user_rows.append([user_id, person_id, self.test_config.get('admin_username'),
                        password_hash, salt_b64, 'Admin', 'active'])
        
        admin_rows.append([admin_id, person_id, self.test_config.get('admin_code'), self.test_config.get('admin_position'), 'active'])

        self.data['admins'].append({'admin_id': admin_id, 'person_id': person_id})
        
        self.add_statement(f"-- ADMIN IDs: person={person_id}, user={user_id}, admin={admin_id}")
        
        # Insert all fixed accounts - FIXED: profile_picture instead of profile_picture_url
        self.bulk_insert('person', ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 'phone_number', 'citizen_id', 'address', 'profile_picture'], person_rows)
        self.bulk_insert('user_account', ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 'role_name', 'account_status'], user_rows)
        self.bulk_insert('instructor', ['instructor_id', 'person_id', 'instructor_code', 'degree', 'specialization', 'department_id', 'hire_date', 'employment_status'], instructor_rows)
        self.bulk_insert('admin', ['admin_id', 'person_id', 'admin_code', 'position', 'admin_status'], admin_rows)

    def create_regular_staff(self):
        self.add_statement("\n-- ==================== REGULAR INSTRUCTORS & ADMINS ====================")
        
        first_names = self.names_config.get('first_names', '').split(', ')
        middle_names = self.names_config.get('middle_names', '').split(', ')
        last_names_male = self.names_config.get('last_names_male', '').split(', ')
        last_names_female = self.names_config.get('last_names_female', '').split(', ')
        
        person_rows = []
        user_rows = []
        instructor_rows = []
        admin_rows = []
        
        # Instructors
        num_instructors = int(self.staff_config.get('regular_instructors', 12))
        for i in range(num_instructors):
            gender = random.choice(['male', 'female'])
            last_pool = last_names_male if gender == 'male' else last_names_female
            
            person_id = self.generate_uuid()
            full_name = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_pool)}"
            email = f"gv{i+1:02d}@edu.vn"
            phone = f"0{random.randint(300000000, 999999999)}"
            dob = date(random.randint(1970, 1990), random.randint(1, 12), random.randint(1, 28))
            
            citizen_id = f"{random.randint(100000000000, 999999999999)}"
            
            # Get random profile picture
            profile_pic = self.media_scanner.get_random_file('profile_pics')
            profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
            
            person_rows.append([person_id, full_name, dob, gender, email, phone, citizen_id, 'TP Hồ Chí Minh', profile_pic_url])
            
            user_id = self.generate_uuid()
            username = f"gv{i+1:02d}"
            user_rows.append([user_id, person_id, username, 'hashed_pwd', 'salt', 'Instructor', 'active'])
            
            instructor_id = self.generate_uuid()
            degree = random.choice(['Tiến sĩ', 'Thạc sĩ', 'Cử nhân'])
            specialization = random.choice(['Công nghệ thông tin', 'Kinh tế', 'Kỹ thuật', 'Khoa học'])
            hire_date = date(random.randint(2010, 2020), random.randint(1, 12), 1)
            instructor_rows.append([instructor_id, person_id, f"GV{i+1:04d}", degree, specialization, None, hire_date, 'active'])
            
            self.data['instructors'].append({'instructor_id': instructor_id, 'person_id': person_id, 'full_name': full_name})
        
        # Admins
        num_admins = int(self.staff_config.get('regular_admins', 2))
        for i in range(num_admins):
            person_id = self.generate_uuid()
            full_name = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_names_male)}"
            email = f"admin{i+1}@edu.vn"
            phone = f"0{random.randint(300000000, 999999999)}"
            
            citizen_id = f"{random.randint(100000000000, 999999999999)}"
            
            # Get random profile picture
            profile_pic = self.media_scanner.get_random_file('profile_pics')
            profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
            
            person_rows.append([person_id, full_name, date(1975, 1, 1), 'male', email, phone, citizen_id, 'TP Hồ Chí Minh', profile_pic_url])
            
            user_id = self.generate_uuid()
            username = f"admin{i+1}"
            user_rows.append([user_id, person_id, username, 'hashed_pwd', 'salt', 'Admin', 'active'])
            
            admin_id = self.generate_uuid()
            admin_rows.append([admin_id, person_id, f"AD{i+1:04d}", 'Quản trị viên', 'active'])
            
            self.data['admins'].append({'admin_id': admin_id, 'person_id': person_id})
        
        # FIXED: profile_picture instead of profile_picture_url
        self.bulk_insert('person', ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 'phone_number', 'citizen_id', 'address', 'profile_picture'], person_rows)
        self.bulk_insert('user_account', ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 'role_name', 'account_status'], user_rows)
        self.bulk_insert('instructor', ['instructor_id', 'person_id', 'instructor_code', 'degree', 'specialization', 'department_id', 'hire_date', 'employment_status'], instructor_rows)
        self.bulk_insert('admin', ['admin_id', 'person_id', 'admin_code', 'position', 'admin_status'], admin_rows)    
    
    def create_faculties_and_departments(self):
        self.add_statement("\n-- ==================== FACULTIES & DEPARTMENTS ====================")
        
        faculty_rows = []
        department_rows = []
        
        for line in self.spec_data.get('faculties', []):
            parts = [p.strip() for p in line.split('|')]
            fac_name, fac_code, dept_names = parts[0], parts[1], [d.strip() for d in parts[2].split(',')]
            
            faculty_id = self.generate_uuid()
            dean_id = random.choice(self.data['instructors'])['instructor_id']
            
            self.data['faculties'].append({'faculty_id': faculty_id, 'faculty_name': fac_name, 'faculty_code': fac_code})
            # FIXED: Changed 'status' to 'faculty_status'
            faculty_rows.append([faculty_id, fac_name, fac_code, dean_id, 'active'])
            
            for idx, dept_name in enumerate(dept_names):
                dept_id = self.generate_uuid()
                dept_code = f"{fac_code}D{idx+1}"
                head_id = random.choice(self.data['instructors'])['instructor_id']
                
                self.data['departments'].append({
                    'department_id': dept_id,
                    'department_name': dept_name,
                    'faculty_id': faculty_id
                })
                # FIXED: Removed 'status' column (doesn't exist in new schema)
                department_rows.append([dept_id, dept_name, dept_code, faculty_id, head_id])
        
        # FIXED: Changed 'status' to 'faculty_status'
        self.bulk_insert('faculty', ['faculty_id', 'faculty_name', 'faculty_code', 'dean_id', 'faculty_status'], faculty_rows)
        # FIXED: Removed 'status' column
        self.bulk_insert('department', ['department_id', 'department_name', 'department_code', 'faculty_id', 'head_of_department_id'], department_rows)

    def create_academic_years_and_semesters(self):
        self.add_statement("\n-- ==================== ACADEMIC YEARS & SEMESTERS ====================")
        
        ay_rows = []
        sem_rows = []
        
        academic_years_config = self.spec_data.get('academic_years_config', {})
        
        for year_range, details in academic_years_config.items():
            date_range = details.split('to')
            start_date = datetime.strptime(date_range[0].strip(), '%Y-%m-%d').date()
            end_date = datetime.strptime(date_range[1].split(',')[0].strip(), '%Y-%m-%d').date()
            status = details.split(',')[1].strip()
            
            academic_year_id = self.generate_uuid()
            start_year = int(year_range.split('-')[0])
            end_year = int(year_range.split('-')[1])
            
            self.data['academic_years'].append({
                'academic_year_id': academic_year_id,
                'start_year': start_year,
                'end_year': end_year
            })
            
            # FIXED: Added 'year_name' (required in new schema), changed 'status' to 'academic_year_status'
            ay_rows.append([academic_year_id, year_range, start_date, end_date, status])
            
            # Generate semesters
            semesters_info = [
                ('fall', f'Học kỳ 1 ({start_year}-{end_year})', date(start_year, 9, 1), date(start_year, 12, 31)),
                ('spring', f'Học kỳ 2 ({start_year}-{end_year})', date(end_year, 1, 1), date(end_year, 5, 31)),
                ('summer', f'Học kỳ hè ({start_year}-{end_year})', date(end_year, 6, 1), date(end_year, 8, 31))
            ]
            
            for sem_type, sem_name, sem_start, sem_end in semesters_info:
                semester_id = self.generate_uuid()
                
                self.data['semesters'].append({
                    'semester_id': semester_id,
                    'semester_name': sem_name,
                    'semester_type': sem_type,
                    'academic_year_id': academic_year_id,
                    'start_year': start_year,
                    'end_year': end_year,
                    'start_date': sem_start,
                    'end_date': sem_end
                })
                
                reg_start = sem_start - timedelta(days=30)
                reg_end = sem_start - timedelta(days=7)
                
                # FIXED: Changed 'status' to 'semester_status'
                sem_rows.append([semester_id, sem_name, academic_year_id, sem_type, sem_start, sem_end, reg_start, reg_end, 'active'])
        
        # FIXED: Added 'year_name', changed 'status' to 'academic_year_status'
        self.bulk_insert('academic_year', ['academic_year_id', 'year_name', 'start_date', 'end_date', 'academic_year_status'], ay_rows)
        # FIXED: Changed 'status' to 'semester_status'
        self.bulk_insert('semester', ['semester_id', 'semester_name', 'academic_year_id', 'semester_type', 'start_date', 'end_date', 'registration_start_date', 'registration_end_date', 'semester_status'], sem_rows)

    def create_classes(self):
        self.add_statement("\n-- ==================== CLASSES ====================")
        
        class_rows = []
        class_names = set()
        
        for line in self.spec_data.get('class_curricula', []):
            parts = [p.strip() for p in line.split('|')]
            class_name = parts[0]
            dept_name = parts[1]
            
            if class_name in class_names:
                continue
            class_names.add(class_name)
            
            # Extract year from class name (e.g., K2023-1 -> 2023)
            year = int(class_name[1:5])
            
            # Find matching academic year and department
            matching_ay = next((ay for ay in self.data['academic_years'] if ay['start_year'] == year), None)
            matching_dept = next((d for d in self.data['departments'] if d['department_name'] == dept_name), None)
            
            if not matching_ay or not matching_dept:
                continue
            
            class_id = self.generate_uuid()
            class_code = class_name
            advisor_id = random.choice(self.data['instructors'])['instructor_id']
            
            self.data['classes'].append({
                'class_id': class_id,
                'class_code': class_code,
                'class_name': class_name,
                'department_id': matching_dept['department_id'],
                'start_academic_year_id': matching_ay['academic_year_id'],
                'start_year': year,
                'department_name': dept_name
            })
            
            # FIXED: Added 'department_id' and 'advisor_instructor_id', changed 'status' to 'class_status'
            class_rows.append([class_id, class_code, class_name, matching_dept['department_id'], 
                            advisor_id, matching_ay['academic_year_id'], 'active'])
        
        # FIXED: Added 'department_id' and 'advisor_instructor_id', changed 'status' to 'class_status'
        self.bulk_insert('class', ['class_id', 'class_code', 'class_name', 'department_id', 
                                'advisor_instructor_id', 'start_academic_year_id', 'class_status'], class_rows)

    def create_subjects(self):
        self.add_statement("\n-- ==================== SUBJECTS ====================")
        
        subject_rows = []
        
        # Get first department as default for general subjects
        default_dept_id = self.data['departments'][0]['department_id']
        
        # General subjects
        for line in self.spec_data.get('general_subjects', []):
            parts = [p.strip() for p in line.split('|')]
            subj_name, subj_code, credits, theory, practice = parts
            
            subject_id = self.generate_uuid()
            
            self.data['subjects'].append({
                'subject_id': subject_id,
                'subject_code': subj_code,
                'subject_name': subj_name,
                'credits': int(credits),
                'theory_hours': int(theory),
                'practice_hours': int(practice),
                'is_general': True
            })
            
            # FIXED: Changed 'status' to 'subject_status'
            subject_rows.append([subject_id, subj_name, subj_code, int(credits), int(theory), int(practice), 
                            True, default_dept_id, 'active'])
        
        # Department subjects
        for line in self.spec_data.get('department_subjects', []):
            parts = [p.strip() for p in line.split('|')]
            dept_name, subj_name, subj_code, credits, theory, practice = parts
            
            # Find department
            dept = next((d for d in self.data['departments'] if d['department_name'] == dept_name), None)
            if not dept:
                continue
            
            subject_id = self.generate_uuid()
            
            self.data['subjects'].append({
                'subject_id': subject_id,
                'subject_code': subj_code,
                'subject_name': subj_name,
                'credits': int(credits),
                'theory_hours': int(theory),
                'practice_hours': int(practice),
                'is_general': False,
                'department_id': dept['department_id']
            })
            
            # FIXED: Changed 'status' to 'subject_status'
            subject_rows.append([subject_id, subj_name, subj_code, int(credits), int(theory), int(practice), 
                            False, dept['department_id'], 'active'])
        
        # FIXED: Changed 'status' to 'subject_status'
        self.bulk_insert('subject', ['subject_id', 'subject_name', 'subject_code', 'credits', 'theory_hours', 
                                    'practice_hours', 'is_general', 'department_id', 'subject_status'], subject_rows)

    def create_curriculum_details(self):
        """
        UPDATED: curriculum_detail now links department -> subject -> semester
        NOT class -> subject -> semester
        """
        self.add_statement("\n-- ==================== CURRICULUM DETAILS ====================")
        
        curriculum_rows = []
        
        # Group subjects by department
        subjects_by_dept = defaultdict(list)
        for subject in self.data['subjects']:
            dept_id = subject.get('department_id')
            if dept_id:
                subjects_by_dept[dept_id].append(subject)
        
        # For each department, distribute subjects across semesters
        for dept_id, subjects in subjects_by_dept.items():
            # Get semesters (use recent years)
            recent_semesters = [s for s in self.data['semesters'] 
                            if s['start_year'] >= 2023]
            
            if not recent_semesters:
                continue
            
            # Distribute subjects across semesters (roughly 5-6 per semester)
            subjects_per_semester = 6
            semester_index = 0
            
            for i, subject in enumerate(subjects):
                if semester_index >= len(recent_semesters):
                    semester_index = 0  # Wrap around
                
                semester = recent_semesters[semester_index]
                
                curriculum_detail_id = self.generate_uuid()
                curriculum_rows.append([
                    curriculum_detail_id,
                    dept_id,
                    subject['subject_id'],
                    semester['semester_id']
                ])
                
                # Move to next semester after distributing subjects
                if (i + 1) % subjects_per_semester == 0:
                    semester_index += 1
        
        self.add_statement(f"-- Total curriculum details: {len(curriculum_rows)}")
        
        self.bulk_insert('curriculum_detail',
                        ['curriculum_detail_id', 'department_id', 'subject_id', 'semester_id'],
                        curriculum_rows)

    def create_exams_and_exam_classes(self):
        """
        NEW: Updated for two-table exam structure with PDF files
        - exam: course-level exam definition (with exam PDFs and answer keys)
        - exam_class: specific exam schedule for a course_class
        """
        self.add_statement("\n-- ==================== EXAMS & EXAM CLASSES ====================")
        self.add_statement("-- exam: course-level exam definition with PDF files")
        self.add_statement("-- exam_class: specific exam schedule with room and time")
        
        exam_rows = []
        exam_class_rows = []
        
        # Track created exams by course_id to avoid duplicates
        exams_by_course = {}
        
        # Group course_classes by course
        course_classes_by_course = defaultdict(list)
        for cc in self.data['course_classes']:
            course_classes_by_course[cc['course_id']].append(cc)
        
        for course_id, course_classes in course_classes_by_course.items():
            course = next((c for c in self.data['courses'] if c['course_id'] == course_id), None)
            if not course:
                continue
            
            # Create exam definition for this course (once per course)
            exam_id = self.generate_uuid()
            exam_format = random.choice(['multiple_choice', 'essay', 'practical', 'oral', 'mixed'])
            exam_type = random.choice(['midterm', 'final', 'final', 'final'])  # More finals
            
            # Get random exam PDF and answer key
            exam_pdf = self.media_scanner.get_random_file('course_docs', 'pdf')
            answer_pdf = self.media_scanner.get_random_file('course_docs', 'pdf')
            
            exam_pdf_url = self.media_scanner.build_url('exams', exam_pdf) if exam_pdf else None
            answer_pdf_url = self.media_scanner.build_url('exams', answer_pdf) if answer_pdf else None
            
            exam_rows.append([
                exam_id,
                course_id,
                exam_format,
                exam_type,
                exam_pdf_url,
                answer_pdf_url,
                f"Đề thi {exam_type} - {course.get('subject_name', '')}"
            ])
            
            exams_by_course[course_id] = exam_id
            
            # Create exam_class schedules for each course_class
            semester = next((s for s in self.data['semesters'] 
                            if s['semester_id'] == course['semester_id']), None)
            
            if not semester:
                continue
            
            # Exam period: last 2 weeks of semester
            sem_end = semester['end_date']
            exam_start = sem_end - timedelta(days=14)
            
            # Generate exam dates (weekdays only)
            exam_dates = []
            current = exam_start
            while current <= sem_end:
                if current.weekday() < 6:  # Monday to Saturday
                    exam_dates.append(current)
                current += timedelta(days=1)
            
            if not exam_dates:
                continue
            
            # Exam time slots
            exam_slots = [
                (7, 30, 120),   # 7:30 AM, 2 hours
                (10, 0, 120),   # 10:00 AM, 2 hours
                (13, 30, 120),  # 1:30 PM, 2 hours
                (16, 0, 120),   # 4:00 PM, 2 hours
            ]
            
            # Track room usage: (room_id, datetime) -> True
            exam_room_usage = {}
            
            for cc in course_classes:
                # Try to schedule exam without conflicts
                exam_scheduled = False
                
                for attempt in range(20):
                    exam_date = random.choice(exam_dates)
                    hour, minute, duration = random.choice(exam_slots)
                    start_time = datetime.combine(exam_date, datetime.min.time().replace(hour=hour, minute=minute))
                    room = random.choice(self.data['rooms'])
                    
                    key = (room['room_id'], start_time)
                    if key not in exam_room_usage:
                        exam_room_usage[key] = True
                        
                        exam_class_id = self.generate_uuid()
                        monitor_instructor = random.choice(self.data['instructors'])
                        
                        exam_class_rows.append([
                            exam_class_id,
                            exam_id,
                            cc['course_class_id'],
                            room['room_id'],
                            monitor_instructor['instructor_id'],
                            start_time,
                            duration,
                            'scheduled'
                        ])
                        
                        exam_scheduled = True
                        break
                
                if not exam_scheduled:
                    # Fallback: schedule anyway (may conflict)
                    exam_date = random.choice(exam_dates)
                    hour, minute, duration = random.choice(exam_slots)
                    start_time = datetime.combine(exam_date, datetime.min.time().replace(hour=hour, minute=minute))
                    room = random.choice(self.data['rooms'])
                    
                    exam_class_id = self.generate_uuid()
                    monitor_instructor = random.choice(self.data['instructors'])
                    
                    exam_class_rows.append([
                        exam_class_id,
                        exam_id,
                        cc['course_class_id'],
                        room['room_id'],
                        monitor_instructor['instructor_id'],
                        start_time,
                        duration,
                        'scheduled'
                    ])
        
        self.add_statement(f"-- Total exams (course-level): {len(exam_rows)}")
        self.add_statement(f"-- Total exam_class (scheduled): {len(exam_class_rows)}")
        
        # Insert exam definitions
        self.bulk_insert('exam',
                        ['exam_id', 'course_id', 'exam_format', 'exam_type', 
                        'exam_file_pdf', 'answer_key_pdf', 'notes'],
                        exam_rows)
        
        # Insert exam_class schedules
        self.bulk_insert('exam_class',
                        ['exam_class_id', 'exam_id', 'course_class_id', 'room_id',
                        'monitor_instructor_id', 'start_time', 'duration_minutes', 'exam_status'],
                        exam_class_rows)

    def create_student_enrollments(self):
        """
        UPDATED: Track enrollment IDs and course info for payment generation
        Fixed: Added deduplication to prevent UNIQUE constraint violations
        """
        self.add_statement("\n-- ==================== STUDENT COURSE ENROLLMENTS (REALISTIC & MASSIVE) ====================")
        self.add_statement("-- Students enrolled with STRICT schedule conflict checking")
        self.add_statement("-- Fixed STUDENT account gets deterministic grades for testing")
        
        enrollment_rows = []
        
        # IMPORTANT: Initialize enrollments list to track IDs and course info
        self.data['enrollments'] = []
        
        # Track enrollments to prevent duplicates: (student_id, course_class_id) -> True
        enrolled_combinations = set()
        
        # Group course_classes by course_id
        course_classes_by_course = defaultdict(list)
        for cc in self.data['course_classes']:
            course_classes_by_course[cc['course_id']].append(cc)
        
        att_min = float(self.enrollment_config.get('attendance_min', 7.0))
        att_max = float(self.enrollment_config.get('attendance_max', 10.0))
        mid_min = float(self.enrollment_config.get('midterm_min', 5.0))
        mid_max = float(self.enrollment_config.get('midterm_max', 9.5))
        fin_min = float(self.enrollment_config.get('final_min', 5.0))
        fin_max = float(self.enrollment_config.get('final_max', 9.5))
        
        # Track each student's schedule: student_id -> {semester_id: [(day, start_period, end_period), ...]}
        student_schedules = defaultdict(lambda: defaultdict(list))
        
        conflict_count = 0
        skipped_count = 0
        duplicate_count = 0
        
        for student in self.data['students']:
            class_id = student['class_id']
            cls = next((c for c in self.data['classes'] if c['class_id'] == class_id), None)
            if not cls or 'curriculum' not in cls:
                continue
            
            curriculum_subject_ids = {s['subject_id'] for s in cls['curriculum']}
            is_fixed = student.get('is_fixed', False)
            student_start_year = student['class_start_year']
            
            # Get all courses this student should take
            student_courses = []
            for course in self.data['courses']:
                if course['subject_id'] not in curriculum_subject_ids:
                    continue
                
                # Only enroll in courses at or after student's start year
                if course['start_year'] < student_start_year:
                    continue
                
                # Don't enroll in future semesters (after Fall 2025)
                if course['start_year'] > 2025:
                    continue
                if course['start_year'] == 2025 and course['semester_type'] == 'summer':
                    continue  # Skip summer 2025 (future)
                
                student_courses.append(course)
            
            # Sort courses by semester for proper scheduling
            semester_order = {'fall': 1, 'spring': 2, 'summer': 3}
            student_courses.sort(key=lambda c: (c['start_year'], semester_order.get(c['semester_type'], 0)))
            
            for course in student_courses:
                # Find available course_class sections for this course
                available_classes = course_classes_by_course.get(course['course_id'], [])
                if not available_classes:
                    continue
                
                # Try to find a course_class section without schedule conflicts
                assigned_course_class = None
                
                for cc in available_classes:
                    # CHECK FOR DUPLICATE ENROLLMENT FIRST
                    enrollment_key = (student['student_id'], cc['course_class_id'])
                    if enrollment_key in enrolled_combinations:
                        duplicate_count += 1
                        continue
                    
                    # Check if this course_class conflicts with student's existing schedule IN THIS SEMESTER
                    has_conflict = False
                    
                    semester_schedule = student_schedules[student['student_id']][cc['semester_id']]
                    
                    # Check each day this course_class meets
                    for day in cc['days']:
                        for existing_schedule in semester_schedule:
                            existing_day, existing_start, existing_end = existing_schedule
                            
                            # Check if same day
                            if day == existing_day:
                                # Check time overlap
                                if not (cc['end_period'] < existing_start or cc['start_period'] > existing_end):
                                    has_conflict = True
                                    conflict_count += 1
                                    break
                        
                        if has_conflict:
                            break
                    
                    # Check if section is full
                    if not has_conflict:
                        if cc['enrolled_count'] < cc['max_students']:
                            assigned_course_class = cc
                            cc['enrolled_count'] += 1
                            break
                
                # If NO conflict-free section found, SKIP this enrollment
                if not assigned_course_class:
                    skipped_count += 1
                    if is_fixed:
                        self.add_statement(f"-- SKIPPED: STUDENT (fixed) - {course['subject_code']} in {course['start_year']} {course['semester_type']} (No conflict-free section)")
                    continue
                
                # MARK AS ENROLLED (prevent duplicates)
                enrollment_key = (student['student_id'], assigned_course_class['course_class_id'])
                enrolled_combinations.add(enrollment_key)
                
                # Add to student's schedule for THIS SEMESTER
                for day in assigned_course_class['days']:
                    student_schedules[student['student_id']][assigned_course_class['semester_id']].append((
                        day,
                        assigned_course_class['start_period'],
                        assigned_course_class['end_period']
                    ))
                
                enrollment_id = self.generate_uuid()
                
                # Determine if this is a past, current, or future semester
                is_past_semester = (course['start_year'] < 2025) or \
                                (course['start_year'] == 2025 and course['semester_type'] == 'spring')
                is_current_semester = (course['start_year'] == 2025 and course['semester_type'] == 'fall')
                
                if is_fixed:
                    # FIXED STUDENT ACCOUNT - DETERMINISTIC GRADES
                    if is_past_semester:
                        # ALL past semesters: COMPLETED with full grades
                        attendance = round(random.uniform(7.5, 9.5), 2)
                        midterm = round(random.uniform(6.5, 9.0), 2)
                        final = round(random.uniform(7.0, 9.5), 2)
                        status = 'completed'
                        
                    elif is_current_semester:
                        # Fall 2025: IN PROGRESS - ALL have attendance + midterm, NO finals
                        attendance = round(random.uniform(7.5, 9.5), 2)
                        midterm = round(random.uniform(6.5, 9.0), 2)
                        final = None
                        status = 'registered'
                        
                    else:
                        # Future semesters: SKIP
                        continue
                        
                else:
                    # REGULAR STUDENTS - VARIED GRADES
                    if is_past_semester:
                        # Past semesters: Completed with full grades
                        attendance = round(random.uniform(att_min, att_max), 2)
                        midterm = round(random.uniform(mid_min, mid_max), 2)
                        final = round(random.uniform(fin_min, fin_max), 2)
                        status = 'completed'
                        
                    elif is_current_semester:
                        # Fall 2025: In progress - varied completion
                        rand = random.random()
                        if rand < 0.60:  # 60% have midterm done
                            attendance = round(random.uniform(att_min, att_max), 2)
                            midterm = round(random.uniform(mid_min, mid_max), 2)
                            final = None
                        elif rand < 0.85:  # 25% have only attendance
                            attendance = round(random.uniform(att_min, att_max), 2)
                            midterm = None
                            final = None
                        else:  # 15% not started
                            attendance = None
                            midterm = None
                            final = None
                        status = 'registered'
                        
                    else:
                        # Future semesters: SKIP
                        continue
                
                # Insert enrollment
                enrollment_rows.append([
                    enrollment_id,
                    student['student_id'],
                    assigned_course_class['course_class_id'],
                    course['semester_start'],
                    status,
                    None,  # cancellation_date
                    None,  # cancellation_reason
                    attendance,
                    midterm,
                    final
                ])
                
                # STORE enrollment data for payment generation (with course info)
                self.data['enrollments'].append({
                    'enrollment_id': enrollment_id,
                    'student_id': student['student_id'],
                    'course_class_id': assigned_course_class['course_class_id'],
                    'course_id': course['course_id'],  # Store course_id
                    'semester_id': course['semester_id'],  # Store semester_id
                    'credits': course['credits'],
                    'enrollment_date': course['semester_start'],
                    'status': status
                })
                
                # Log fixed student enrollments for debugging
                if is_fixed:
                    grade_status = "FULL GRADES" if final is not None else \
                                "ATT+MID" if midterm is not None else \
                                "ATT ONLY" if attendance is not None else "NO GRADES"
                    self.add_statement(f"-- ENROLLED: STUDENT (fixed) - {course['subject_code']} - {course['start_year']} {course['semester_type']} - {grade_status}")
        
        self.add_statement(f"\n-- ========================================")
        self.add_statement(f"-- ENROLLMENT SUMMARY")
        self.add_statement(f"-- ========================================")
        self.add_statement(f"-- Total enrollments created: {len(enrollment_rows)}")
        self.add_statement(f"-- Schedule conflicts detected: {conflict_count}")
        self.add_statement(f"-- Duplicate enrollments prevented: {duplicate_count}")
        self.add_statement(f"-- Enrollments skipped (no conflict-free slot): {skipped_count}")
        
        # REMOVED is_paid column from insert
        self.bulk_insert('student_enrollment',
                        ['enrollment_id', 'student_id', 'course_class_id', 'enrollment_date',
                        'enrollment_status', 'cancellation_date', 'cancellation_reason',
                        'attendance_grade', 'midterm_grade', 'final_grade'],
                        enrollment_rows)

    # ==================== CURRICULUM MAPPING ====================
    def map_class_curricula(self):
        self.add_statement("\n-- ==================== MAPPING CLASS CURRICULA ====================")
        
        # Build subject code lookup
        subject_lookup = {s['subject_code']: s for s in self.data['subjects']}
        general_subject_codes = [s['subject_code'] for s in self.data['subjects'] if s.get('is_general')]
        
        self.add_statement(f"-- Total subjects available: {len(subject_lookup)}")
        self.add_statement(f"-- General subjects: {len(general_subject_codes)}")
        
        for cls in self.data['classes']:
            # Find curriculum line for this class
            curriculum_line = None
            for line in self.spec_data.get('class_curricula', []):
                if line.strip().startswith(cls['class_code']):
                    curriculum_line = line
                    break
            
            if not curriculum_line:
                self.add_statement(f"-- WARNING: No curriculum found for {cls['class_code']}")
                cls['curriculum'] = []
                continue
            
            parts = [p.strip() for p in curriculum_line.split('|')]
            if len(parts) < 3:
                self.add_statement(f"-- WARNING: Invalid curriculum line for {cls['class_code']}")
                cls['curriculum'] = []
                continue
            
            subject_codes_str = parts[2]
            
            # Parse subject codes
            subject_codes = []
            for code in subject_codes_str.split(','):
                code = code.strip()
                if code == '@ALL_GENERAL':
                    subject_codes.extend(general_subject_codes)
                else:
                    subject_codes.append(code)
            
            # Map to subject objects
            curriculum_subjects = []
            missing_codes = []
            for code in subject_codes:
                if code in subject_lookup:
                    curriculum_subjects.append(subject_lookup[code])
                else:
                    missing_codes.append(code)
            
            cls['curriculum'] = curriculum_subjects
            
            if missing_codes:
                self.add_statement(f"-- WARNING: {cls['class_code']} missing subjects: {', '.join(missing_codes)}")
            
            self.add_statement(f"-- {cls['class_code']}: {len(curriculum_subjects)} subjects mapped")
    
    def create_students(self):
        self.add_statement("\n-- ==================== STUDENTS ====================")
        
        first_names = self.names_config.get('first_names', '').split(', ')
        middle_names = self.names_config.get('middle_names', '').split(', ')
        last_names_male = self.names_config.get('last_names_male', '').split(', ')
        last_names_female = self.names_config.get('last_names_female', '').split(', ')
        
        students_per_class = int(self.students_config.get('students_per_class', 30))
        global_counter = 1
        
        person_rows = []
        user_rows = []
        student_rows = []
        
        # Fixed STUDENT account - Simple IDs
        password = self.test_config.get('password')
        salt_b64 = self.test_config.get('salt_base64')
        salt_bytes = base64.b64decode(salt_b64)
        password_hash = self.create_password_hash(password, salt_bytes)
        
        target_class_year = int(self.test_config.get('student_class_year', 2023))
        target_class = next((c for c in self.data['classes'] if c['start_year'] == target_class_year), None)
        
        if target_class:
            person_id = self.test_config.get('student_person_id', '00000000-0000-0000-0000-000000000001')
            user_id = self.test_config.get('student_user_id', '00000000-0000-0000-0000-000000000002')
            student_id = self.test_config.get('student_id', '00000000-0000-0000-0000-000000000003')
            
            self.data['fixed_accounts']['student'] = {
                'person_id': person_id,
                'user_id': user_id,
                'student_id': student_id,
                'class_id': target_class['class_id'],
                'class_start_year': target_class_year
            }
            
            fixed_student_citizen_id = f"{random.randint(100000000000, 999999999999)}"
            
            # Get random profile picture for fixed student
            profile_pic = self.media_scanner.get_random_file('profile_pics')
            profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
            
            person_rows.append([person_id, self.test_config.get('student_name'),
                            self.test_config.get('student_dob'),
                            self.test_config.get('student_gender'),
                            self.test_config.get('student_email'),
                            self.test_config.get('student_phone'),
                            fixed_student_citizen_id,
                            'TP Hồ Chí Minh',
                            profile_pic_url])
            
            user_rows.append([user_id, person_id, self.test_config.get('student_username'),
                            password_hash, salt_b64, 'Student', 'active'])
            
            student_rows.append([student_id, person_id, self.test_config.get('student_code'),
                                target_class['class_id'], 'active'])
            
            self.data['students'].append({
                'student_id': student_id,
                'person_id': person_id,
                'student_code': self.test_config.get('student_code'),
                'class_id': target_class['class_id'],
                'class_start_year': target_class_year,
                'is_fixed': True
            })
            
            self.add_statement(f"-- Fixed STUDENT: {self.test_config.get('student_username')}")
            self.add_statement(f"-- STUDENT IDs: person={person_id}, user={user_id}, student={student_id}")
        
        # Regular students
        for cls in self.data['classes']:
            for i in range(students_per_class):
                gender = random.choice(['male', 'female'])
                last_pool = last_names_male if gender == 'male' else last_names_female
                
                person_id = self.generate_uuid()
                full_name = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_pool)}"
                birth_year = cls['start_year'] - 18
                dob = date(birth_year, random.randint(1, 12), random.randint(1, 28))
                email = f"sv{global_counter:05d}@edu.vn"
                phone = f"0{random.randint(300000000, 999999999)}"
                
                citizen_id = f"{random.randint(100000000000, 999999999999)}"
                
                # Get random profile picture for regular student
                profile_pic = self.media_scanner.get_random_file('profile_pics')
                profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
                
                person_rows.append([person_id, full_name, dob, gender, email, phone, citizen_id, 'TP Hồ Chí Minh', profile_pic_url])
                
                user_id = self.generate_uuid()
                username = f"sv{global_counter:05d}"
                user_rows.append([user_id, person_id, username, 'hashed_pwd', 'salt', 'Student', 'active'])
                
                student_id = self.generate_uuid()
                student_code = f"SV{global_counter:06d}"
                student_rows.append([student_id, person_id, student_code, cls['class_id'], 'active'])
                
                self.data['students'].append({
                    'student_id': student_id,
                    'person_id': person_id,
                    'student_code': student_code,
                    'class_id': cls['class_id'],
                    'class_start_year': cls['start_year'],
                    'is_fixed': False
                })
                
                global_counter += 1
        
        # FIXED: profile_picture instead of profile_picture_url
        self.bulk_insert('person', ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 'phone_number', 'citizen_id', 'address', 'profile_picture'], person_rows)
        self.bulk_insert('user_account', ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 'role_name', 'account_status'], user_rows)
        self.bulk_insert('student', ['student_id', 'person_id', 'student_code', 'class_id', 'enrollment_status'], student_rows)

    def create_buildings_and_rooms(self):
        self.add_statement("\n-- ==================== BUILDINGS & ROOMS ====================")
        
        building_rows = []
        room_rows = []
        
        # Valid room types from schema
        room_types = [
            'exam',
            'lecture_hall',
            'classroom',
            'computer_lab',
            'laboratory',
            'meeting_room',
            'gym_room',
            'swimming_pool',
            'music_room',
            'art_room',
            'library_room',
            'self_study_room',
            'dorm_room'
        ]
        
        # Room type distribution (weighted for realistic campus)
        room_type_weights = {
            'classroom': 0.35,
            'lecture_hall': 0.15,
            'computer_lab': 0.15,
            'laboratory': 0.10,
            'exam': 0.10,
            'meeting_room': 0.05,
            'self_study_room': 0.05,
            'library_room': 0.03,
            'gym_room': 0.01,
            'music_room': 0.003,
            'art_room': 0.003,
            'swimming_pool': 0.001,
            'dorm_room': 0.003
        }
        
        # Capacity ranges by room type
        capacity_by_type = {
            'exam': (50, 100),
            'lecture_hall': (100, 300),
            'classroom': (30, 60),
            'computer_lab': (30, 50),
            'laboratory': (20, 40),
            'meeting_room': (10, 30),
            'gym_room': (50, 100),
            'swimming_pool': (30, 50),
            'music_room': (15, 30),
            'art_room': (20, 40),
            'library_room': (50, 150),
            'self_study_room': (20, 50),
            'dorm_room': (2, 4)
        }
        
        for line in self.spec_data.get('buildings', []):
            parts = [p.strip() for p in line.split('|')]
            bldg_name, bldg_code, rooms_count = parts[0], parts[1], int(parts[2])
            
            building_id = self.generate_uuid()
            self.data['buildings'].append({'building_id': building_id, 'building_name': bldg_name})
            building_rows.append([building_id, bldg_name, bldg_code, 'TP Hồ Chí Minh', 'active'])
            
            bldg_letter = bldg_code[-1]
            
            # Distribute room types across this building
            for j in range(rooms_count):
                room_id = self.generate_uuid()
                room_code = f"{bldg_letter}{j+1:02d}"
                
                # Select room type based on weights
                rand = random.random()
                cumulative = 0
                selected_type = 'classroom'  # default
                
                for rtype, weight in room_type_weights.items():
                    cumulative += weight
                    if rand <= cumulative:
                        selected_type = rtype
                        break
                
                # Get capacity range for this room type
                cap_min, cap_max = capacity_by_type.get(selected_type, (30, 60))
                capacity = random.randint(cap_min, cap_max)
                
                # Generate room name based on type
                room_name_map = {
                    'exam': 'Phòng thi',
                    'lecture_hall': 'Giảng đường',
                    'classroom': 'Phòng học',
                    'computer_lab': 'Phòng máy tính',
                    'laboratory': 'Phòng thí nghiệm',
                    'meeting_room': 'Phòng họp',
                    'gym_room': 'Phòng thể dục',
                    'swimming_pool': 'Hồ bơi',
                    'music_room': 'Phòng âm nhạc',
                    'art_room': 'Phòng mỹ thuật',
                    'library_room': 'Phòng thư viện',
                    'self_study_room': 'Phòng tự học',
                    'dorm_room': 'Ký túc xá'
                }
                
                room_name = f"{room_name_map.get(selected_type, 'Phòng')} {room_code}"
                
                # Get random room picture
                room_pic = self.media_scanner.get_random_file('room_pics')
                room_pic_url = self.media_scanner.build_url('room_pics', room_pic) if room_pic else None
                
                # FIXED: Changed 'picture_url' to 'room_picture_path'
                self.data['rooms'].append({
                    'room_id': room_id, 
                    'room_code': room_code, 
                    'room_name': room_name,
                    'capacity': capacity,
                    'room_type': selected_type,
                    'room_picture_path': room_pic_url
                })
                
                room_rows.append([
                    room_id, 
                    room_code, 
                    room_name, 
                    capacity, 
                    selected_type,
                    building_id, 
                    'active',
                    room_pic_url
                ])
        
        self.add_statement(f"-- Total buildings: {len(building_rows)}")
        self.add_statement(f"-- Total rooms: {len(room_rows)}")
        
        # Room type distribution summary
        type_counts = {}
        for room in self.data['rooms']:
            rtype = room['room_type']
            type_counts[rtype] = type_counts.get(rtype, 0) + 1
        
        self.add_statement("-- Room type distribution:")
        for rtype, count in sorted(type_counts.items()):
            self.add_statement(f"--   {rtype}: {count}")
        
        self.bulk_insert('building', 
                        ['building_id', 'building_name', 'building_code', 'address', 'building_status'], 
                        building_rows)
        
        self.bulk_insert('room', 
                        ['room_id', 'room_code', 'room_name', 'capacity', 'room_type', 'building_id', 'room_status', 'room_picture_path'], 
                        room_rows)

    def create_room_amenities(self):
        """
        Create room amenities (facilities/equipment available in rooms)
        """
        self.add_statement("\n-- ==================== ROOM AMENITIES ====================")
        
        amenity_rows = []
        
        # Define standard amenities
        amenities = [
            # Basic equipment
            'Máy chiếu (Projector)',
            'Bảng trắng (Whiteboard)',
            'Bảng đen (Blackboard)',
            'Màn hình chiếu (Projection screen)',
            'Loa âm thanh (Audio speakers)',
            'Micro (Microphone)',
            
            # Technology
            'Máy tính giảng viên (Instructor PC)',
            'Kết nối Internet (Internet connection)',
            'WiFi',
            'Hệ thống âm thanh (Sound system)',
            'Camera giám sát (Security camera)',
            'Màn hình tương tác (Interactive display)',
            
            # Comfort
            'Điều hòa không khí (Air conditioning)',
            'Quạt trần (Ceiling fans)',
            'Cửa sổ lớn (Large windows)',
            'Rèm che (Curtains/Blinds)',
            'Ghế có đệm (Cushioned chairs)',
            'Bàn học điều chỉnh (Adjustable desks)',
            
            # Specialized equipment
            'Thiết bị thí nghiệm (Lab equipment)',
            'Tủ hóa chất (Chemical storage)',
            'Máy tính cá nhân (PC stations)',
            'Bàn vẽ (Drawing tables)',
            'Nhạc cụ (Musical instruments)',
            'Thiết bị thể dục (Gym equipment)',
            'Tủ đồ cá nhân (Personal lockers)',
            'Giường nằm (Beds)',
            'Tủ quần áo (Wardrobes)',
            'Kệ sách (Bookshelves)',
            'Đèn đọc sách (Reading lights)'
        ]
        
        for amenity_name in amenities:
            amenity_id = self.generate_uuid()
            
            self.data['amenities'].append({
                'amenity_id': amenity_id,
                'amenity_name': amenity_name
            })
            
            amenity_rows.append([amenity_id, amenity_name])
        
        self.add_statement(f"-- Total amenities: {len(amenity_rows)}")
        
        self.bulk_insert('room_amenity',
                        ['amenity_id', 'amenity_name'],
                        amenity_rows)


    def create_room_amenity_mappings(self):
        """
        Map amenities to rooms based on room type
        """
        self.add_statement("\n-- ==================== ROOM AMENITY MAPPINGS ====================")
        
        mapping_rows = []
        
        # Get amenity lookup by name
        amenity_lookup = {}
        for amenity in self.data['amenities']:
            # Extract English part from name for easier matching
            name = amenity['amenity_name']
            if '(' in name:
                key = name.split('(')[0].strip()
            else:
                key = name
            amenity_lookup[key] = amenity['amenity_id']
        
        # Define amenities by room type
        amenities_by_type = {
            'exam': [
                'Máy chiếu',
                'Điều hòa không khí',
                'Camera giám sát',
                'Bàn học điều chỉnh',
                'Ghế có đệm'
            ],
            'lecture_hall': [
                'Máy chiếu',
                'Màn hình chiếu',
                'Loa âm thanh',
                'Micro',
                'Bảng trắng',
                'Điều hòa không khí',
                'Máy tính giảng viên',
                'Hệ thống âm thanh',
                'WiFi',
                'Kết nối Internet'
            ],
            'classroom': [
                'Máy chiếu',
                'Bảng trắng',
                'Điều hòa không khí',
                'WiFi',
                'Kết nối Internet',
                'Cửa sổ lớn',
                'Rèm che'
            ],
            'computer_lab': [
                'Máy tính cá nhân',
                'Máy chiếu',
                'Điều hòa không khí',
                'Bảng trắng',
                'WiFi',
                'Kết nối Internet',
                'Máy tính giảng viên'
            ],
            'laboratory': [
                'Thiết bị thí nghiệm',
                'Tủ hóa chất',
                'Bảng trắng',
                'Điều hòa không khí',
                'Cửa sổ lớn',
                'WiFi',
                'Kết nối Internet'
            ],
            'meeting_room': [
                'Máy chiếu',
                'Màn hình tương tác',
                'Bảng trắng',
                'Điều hòa không khí',
                'Hệ thống âm thanh',
                'Micro',
                'WiFi',
                'Kết nối Internet',
                'Ghế có đệm'
            ],
            'gym_room': [
                'Thiết bị thể dục',
                'Tủ đồ cá nhân',
                'Quạt trần',
                'Cửa sổ lớn'
            ],
            'swimming_pool': [
                'Tủ đồ cá nhân',
                'Camera giám sát'
            ],
            'music_room': [
                'Nhạc cụ',
                'Hệ thống âm thanh',
                'Loa âm thanh',
                'Điều hòa không khí',
                'Cửa sổ lớn',
                'Tủ đồ cá nhân'
            ],
            'art_room': [
                'Bàn vẽ',
                'Cửa sổ lớn',
                'Rèm che',
                'Tủ đồ cá nhân',
                'Điều hòa không khí'
            ],
            'library_room': [
                'Kệ sách',
                'Đèn đọc sách',
                'Điều hòa không khí',
                'WiFi',
                'Kết nối Internet',
                'Máy tính cá nhân',
                'Cửa sổ lớn'
            ],
            'self_study_room': [
                'Bàn học điều chỉnh',
                'Ghế có đệm',
                'Đèn đọc sách',
                'Điều hòa không khí',
                'WiFi',
                'Kết nối Internet',
                'Cửa sổ lớn',
                'Rèm che'
            ],
            'dorm_room': [
                'Giường nằm',
                'Tủ quần áo',
                'Bàn học điều chỉnh',
                'Ghế có đệm',
                'Điều hòa không khí',
                'Cửa sổ lớn',
                'WiFi',
                'Kết nối Internet'
            ]
        }
        
        # Map amenities to rooms
        for room in self.data['rooms']:
            room_type = room['room_type']
            amenity_names = amenities_by_type.get(room_type, [])
            
            for amenity_name in amenity_names:
                amenity_id = amenity_lookup.get(amenity_name)
                
                if amenity_id:
                    mapping_id = self.generate_uuid()
                    
                    mapping_rows.append([
                        mapping_id,
                        room['room_id'],
                        amenity_id
                    ])
        
        self.add_statement(f"-- Total room-amenity mappings: {len(mapping_rows)}")
        
        # Statistics
        mappings_per_room_type = {}
        for room in self.data['rooms']:
            rtype = room['room_type']
            room_mappings = [m for m in mapping_rows if m[1] == room['room_id']]
            if rtype not in mappings_per_room_type:
                mappings_per_room_type[rtype] = []
            mappings_per_room_type[rtype].append(len(room_mappings))
        
        self.add_statement("-- Average amenities per room type:")
        for rtype, counts in sorted(mappings_per_room_type.items()):
            avg = sum(counts) / len(counts) if counts else 0
            self.add_statement(f"--   {rtype}: {avg:.1f} amenities")
        
        self.bulk_insert('room_amenity_mapping',
                        ['room_amenity_mapping_id', 'room_id', 'amenity_id'],
                        mapping_rows)

    def create_courses(self):
        self.add_statement("\n-- ==================== COURSES ====================")
        
        course_rows = []
        
        fall_rate = float(self.course_config.get('fall_offering_rate', 0.7))
        spring_rate = float(self.course_config.get('spring_offering_rate', 0.7))
        summer_rate = float(self.course_config.get('summer_offering_rate', 0.3))
        fee = float(self.course_config.get('fee_per_credit', 60))
        
        self.add_statement(f"-- Total subjects available: {len(self.data['subjects'])}")
        self.add_statement(f"-- Total semesters: {len(self.data['semesters'])}")
        
        for semester in self.data['semesters']:
            sem_type = semester['semester_type']
            
            if sem_type == 'fall':
                rate = fall_rate
            elif sem_type == 'spring':
                rate = spring_rate
            else:
                rate = summer_rate
            
            num_to_offer = int(len(self.data['subjects']) * rate)
            subjects_to_offer = random.sample(self.data['subjects'], min(num_to_offer, len(self.data['subjects'])))
            
            self.add_statement(f"-- {semester['semester_name']}: Offering {len(subjects_to_offer)} courses")
            
            for subject in subjects_to_offer:
                course_id = self.generate_uuid()
                
                self.data['courses'].append({
                    'course_id': course_id,
                    'subject_id': subject['subject_id'],
                    'subject_code': subject['subject_code'],
                    'subject_name': subject['subject_name'],
                    'credits': subject['credits'],
                    'theory_hours': subject['theory_hours'],
                    'practice_hours': subject['practice_hours'],
                    'semester_id': semester['semester_id'],
                    'semester_start': semester['start_date'],
                    'semester_end': semester['end_date'],
                    'start_year': semester['start_year'],
                    'semester_type': semester['semester_type']
                })
                
                # FIXED: Removed 'instructor_id' (moved to course_class), changed 'status' to 'course_status'
                course_rows.append([course_id, subject['subject_id'], semester['semester_id'], fee, 'active'])
        
        self.add_statement(f"-- Total courses generated: {len(course_rows)}")
        # FIXED: Removed 'instructor_id', changed 'status' to 'course_status'
        self.bulk_insert('course', ['course_id', 'subject_id', 'semester_id', 'fee_per_credit', 'course_status'], course_rows)

    def create_course_classes(self):
        self.add_statement("\n-- ==================== COURSE CLASSES (REALISTIC SCHEDULING) ====================")
        self.add_statement("-- Each course_class meets on SPECIFIC days at SPECIFIC times")
        self.add_statement("-- Students are assigned to ONE course_class per course")
        
        course_class_rows = []
        
        # Calculate students per course to determine number of class sessions needed
        course_student_counts = defaultdict(set)
        for student in self.data['students']:
            class_id = student['class_id']
            cls = next((c for c in self.data['classes'] if c['class_id'] == class_id), None)
            if not cls or 'curriculum' not in cls:
                continue
            
            curriculum_subject_ids = {s['subject_id'] for s in cls['curriculum']}
            
            for course in self.data['courses']:
                if course['subject_id'] in curriculum_subject_ids:
                    if course['start_year'] >= student['class_start_year']:
                        course_student_counts[course['course_id']].add(student['student_id'])
        
        # Day combinations for scheduling (classes typically meet 2x per week)
        day_combinations = [
            [2, 4],    # Mon, Wed
            [3, 5],    # Tue, Thu
            [2, 5],    # Mon, Thu
            [3, 6],    # Tue, Fri
            [4, 6],    # Wed, Fri
            [2, 3],    # Mon, Tue
            [4, 5],    # Wed, Thu
            [5, 6],    # Thu, Fri
        ]
        
        # Time slots (period ranges)
        time_slots = [
            (1, 3),    # 7:00-9:30
            (4, 6),    # 9:45-12:15
            (7, 9),    # 13:00-15:30
            (10, 12),  # 15:45-18:15
        ]
        
        # Track room usage to avoid conflicts: (room_id, day, period) -> course_class_id
        room_usage = {}
        
        for course in self.data['courses']:
            total_hours = course['theory_hours'] + course['practice_hours']
            if total_hours == 0:
                continue
            
            num_students = len(course_student_counts.get(course['course_id'], set()))
            if num_students == 0:
                continue
            
            # Determine number of class sessions needed (max 50 students per session)
            max_per_session = 50
            num_sessions = max(1, (num_students + max_per_session - 1) // max_per_session)
            
            # Create multiple course_class instances for this course
            for session_idx in range(num_sessions):
                scheduled = False
                attempts = 0
                max_attempts = 100
                
                # Select instructor (use fixed instructor sometimes in fall 2025)
                if course['start_year'] == 2025 and course['semester_type'] == 'fall' and random.random() < 0.3:
                    instructor_id = self.data['fixed_accounts']['instructor']['instructor_id']
                else:
                    instructor_id = random.choice(self.data['instructors'])['instructor_id']
                
                while not scheduled and attempts < max_attempts:
                    attempts += 1
                    
                    # Select random room, days, and time
                    room = random.choice(self.data['rooms'])
                    days = random.choice(day_combinations)
                    time_slot = random.choice(time_slots)
                    
                    # Check for room conflicts on ALL days
                    conflict = False
                    for day in days:
                        for period in range(time_slot[0], time_slot[1] + 1):
                            if (room['room_id'], day, period) in room_usage:
                                conflict = True
                                break
                        if conflict:
                            break
                    
                    if not conflict:
                        # Reserve this room for all days and periods
                        course_class_id = self.generate_uuid()
                        
                        for day in days:
                            for period in range(time_slot[0], time_slot[1] + 1):
                                room_usage[(room['room_id'], day, period)] = course_class_id
                        
                        # Store metadata for student enrollment
                        self.data['course_classes'].append({
                            'course_class_id': course_class_id,
                            'course_id': course['course_id'],
                            'subject_id': course['subject_id'],
                            'subject_code': course['subject_code'],
                            'subject_name': course['subject_name'],
                            'semester_id': course['semester_id'],
                            'semester_start': course['semester_start'],
                            'semester_end': course['semester_end'],
                            'start_year': course['start_year'],
                            'semester_type': course['semester_type'],
                            'instructor_id': instructor_id,
                            'room_id': room['room_id'],
                            'days': days,
                            'start_period': time_slot[0],
                            'end_period': time_slot[1],
                            'max_students': max_per_session,
                            'session_number': session_idx + 1,
                            'enrolled_count': 0
                        })
                        
                        # FIXED: Added 'instructor_id', changed 'status' to 'course_class_status'
                        course_class_rows.append([
                            course_class_id,
                            course['course_id'],
                            instructor_id,  # NEW: instructor_id now in course_class
                            room['room_id'],
                            course['semester_start'],
                            course['semester_end'],
                            max_per_session,
                            days[0],  # ONLY FIRST DAY
                            time_slot[0],
                            time_slot[1],
                            'active'
                        ])
                        
                        scheduled = True
                
                if not scheduled:
                    # Fallback: just use random slot (may have conflicts)
                    course_class_id = self.generate_uuid()
                    room = random.choice(self.data['rooms'])
                    days = random.choice(day_combinations)
                    time_slot = random.choice(time_slots)
                    
                    self.data['course_classes'].append({
                        'course_class_id': course_class_id,
                        'course_id': course['course_id'],
                        'subject_id': course['subject_id'],
                        'subject_code': course['subject_code'],
                        'subject_name': course['subject_name'],
                        'semester_id': course['semester_id'],
                        'semester_start': course['semester_start'],
                        'semester_end': course['semester_end'],
                        'start_year': course['start_year'],
                        'semester_type': course['semester_type'],
                        'instructor_id': instructor_id,
                        'room_id': room['room_id'],
                        'days': days,
                        'start_period': time_slot[0],
                        'end_period': time_slot[1],
                        'max_students': max_per_session,
                        'session_number': session_idx + 1,
                        'enrolled_count': 0
                    })
                    
                    # FIXED: Added 'instructor_id', changed 'status' to 'course_class_status'
                    course_class_rows.append([
                        course_class_id,
                        course['course_id'],
                        instructor_id,  # NEW: instructor_id now in course_class
                        room['room_id'],
                        course['semester_start'],
                        course['semester_end'],
                        max_per_session,
                        days[0],  # ONLY FIRST DAY
                        time_slot[0],
                        time_slot[1],
                        'active'
                    ])
                    
                    self.add_statement(f"-- WARNING: Could not find conflict-free slot for {course['subject_code']} session {session_idx+1}")
        
        self.add_statement(f"-- Generated {len(self.data['course_classes'])} course class sections")
        self.add_statement(f"-- Total course_class records: {len(course_class_rows)}")
        
        # FIXED: Added 'instructor_id', changed 'status' to 'course_class_status'
        self.bulk_insert('course_class', 
                        ['course_class_id', 'course_id', 'instructor_id', 'room_id', 'date_start', 'date_end', 
                        'max_students', 'day_of_week', 'start_period', 'end_period', 'course_class_status'],
                        course_class_rows)

    def create_student_enrollments(self):
        """
        UPDATED: Track enrollment IDs and course info for payment generation
        """
        self.add_statement("\n-- ==================== STUDENT COURSE ENROLLMENTS (REALISTIC & MASSIVE) ====================")
        self.add_statement("-- Students enrolled with STRICT schedule conflict checking")
        self.add_statement("-- Fixed STUDENT account gets deterministic grades for testing")
        
        enrollment_rows = []
        
        # IMPORTANT: Initialize enrollments list to track IDs and course info
        self.data['enrollments'] = []
        
        # Group course_classes by course_id
        course_classes_by_course = defaultdict(list)
        for cc in self.data['course_classes']:
            course_classes_by_course[cc['course_id']].append(cc)
        
        att_min = float(self.enrollment_config.get('attendance_min', 7.0))
        att_max = float(self.enrollment_config.get('attendance_max', 10.0))
        mid_min = float(self.enrollment_config.get('midterm_min', 5.0))
        mid_max = float(self.enrollment_config.get('midterm_max', 9.5))
        fin_min = float(self.enrollment_config.get('final_min', 5.0))
        fin_max = float(self.enrollment_config.get('final_max', 9.5))
        
        # Track each student's schedule: student_id -> {semester_id: [(day, start_period, end_period), ...]}
        student_schedules = defaultdict(lambda: defaultdict(list))
        
        conflict_count = 0
        skipped_count = 0
        
        for student in self.data['students']:
            class_id = student['class_id']
            cls = next((c for c in self.data['classes'] if c['class_id'] == class_id), None)
            if not cls or 'curriculum' not in cls:
                continue
            
            curriculum_subject_ids = {s['subject_id'] for s in cls['curriculum']}
            is_fixed = student.get('is_fixed', False)
            student_start_year = student['class_start_year']
            
            # Get all courses this student should take
            student_courses = []
            for course in self.data['courses']:
                if course['subject_id'] not in curriculum_subject_ids:
                    continue
                
                # Only enroll in courses at or after student's start year
                if course['start_year'] < student_start_year:
                    continue
                
                # Don't enroll in future semesters (after Fall 2025)
                if course['start_year'] > 2025:
                    continue
                if course['start_year'] == 2025 and course['semester_type'] == 'summer':
                    continue  # Skip summer 2025 (future)
                
                student_courses.append(course)
            
            # Sort courses by semester for proper scheduling
            semester_order = {'fall': 1, 'spring': 2, 'summer': 3}
            student_courses.sort(key=lambda c: (c['start_year'], semester_order.get(c['semester_type'], 0)))
            
            for course in student_courses:
                # Find available course_class sections for this course
                available_classes = course_classes_by_course.get(course['course_id'], [])
                if not available_classes:
                    continue
                
                # Try to find a course_class section without schedule conflicts
                assigned_course_class = None
                
                for cc in available_classes:
                    # Check if this course_class conflicts with student's existing schedule IN THIS SEMESTER
                    has_conflict = False
                    
                    semester_schedule = student_schedules[student['student_id']][cc['semester_id']]
                    
                    # Check each day this course_class meets
                    for day in cc['days']:
                        for existing_schedule in semester_schedule:
                            existing_day, existing_start, existing_end = existing_schedule
                            
                            # Check if same day
                            if day == existing_day:
                                # Check time overlap
                                if not (cc['end_period'] < existing_start or cc['start_period'] > existing_end):
                                    has_conflict = True
                                    conflict_count += 1
                                    break
                        
                        if has_conflict:
                            break
                    
                    # Check if section is full
                    if not has_conflict:
                        if cc['enrolled_count'] < cc['max_students']:
                            assigned_course_class = cc
                            cc['enrolled_count'] += 1
                            break
                
                # If NO conflict-free section found, SKIP this enrollment
                if not assigned_course_class:
                    skipped_count += 1
                    if is_fixed:
                        self.add_statement(f"-- SKIPPED: STUDENT (fixed) - {course['subject_code']} in {course['start_year']} {course['semester_type']} (No conflict-free section)")
                    continue
                
                # Add to student's schedule for THIS SEMESTER
                for day in assigned_course_class['days']:
                    student_schedules[student['student_id']][assigned_course_class['semester_id']].append((
                        day,
                        assigned_course_class['start_period'],
                        assigned_course_class['end_period']
                    ))
                
                enrollment_id = self.generate_uuid()
                
                # Determine if this is a past, current, or future semester
                is_past_semester = (course['start_year'] < 2025) or \
                                (course['start_year'] == 2025 and course['semester_type'] == 'spring')
                is_current_semester = (course['start_year'] == 2025 and course['semester_type'] == 'fall')
                
                if is_fixed:
                    # FIXED STUDENT ACCOUNT - DETERMINISTIC GRADES
                    if is_past_semester:
                        # ALL past semesters: COMPLETED with full grades
                        attendance = round(random.uniform(7.5, 9.5), 2)
                        midterm = round(random.uniform(6.5, 9.0), 2)
                        final = round(random.uniform(7.0, 9.5), 2)
                        status = 'completed'
                        
                    elif is_current_semester:
                        # Fall 2025: IN PROGRESS - ALL have attendance + midterm, NO finals
                        attendance = round(random.uniform(7.5, 9.5), 2)
                        midterm = round(random.uniform(6.5, 9.0), 2)
                        final = None
                        status = 'registered'
                        
                    else:
                        # Future semesters: SKIP
                        continue
                        
                else:
                    # REGULAR STUDENTS - VARIED GRADES
                    if is_past_semester:
                        # Past semesters: Completed with full grades
                        attendance = round(random.uniform(att_min, att_max), 2)
                        midterm = round(random.uniform(mid_min, mid_max), 2)
                        final = round(random.uniform(fin_min, fin_max), 2)
                        status = 'completed'
                        
                    elif is_current_semester:
                        # Fall 2025: In progress - varied completion
                        rand = random.random()
                        if rand < 0.60:  # 60% have midterm done
                            attendance = round(random.uniform(att_min, att_max), 2)
                            midterm = round(random.uniform(mid_min, mid_max), 2)
                            final = None
                        elif rand < 0.85:  # 25% have only attendance
                            attendance = round(random.uniform(att_min, att_max), 2)
                            midterm = None
                            final = None
                        else:  # 15% not started
                            attendance = None
                            midterm = None
                            final = None
                        status = 'registered'
                        
                    else:
                        # Future semesters: SKIP
                        continue
                
                # Insert enrollment
                enrollment_rows.append([
                    enrollment_id,
                    student['student_id'],
                    assigned_course_class['course_class_id'],
                    course['semester_start'],
                    status,
                    None,  # cancellation_date
                    None,  # cancellation_reason
                    attendance,
                    midterm,
                    final
                ])
                
                # STORE enrollment data for payment generation (with course info)
                self.data['enrollments'].append({
                    'enrollment_id': enrollment_id,
                    'student_id': student['student_id'],
                    'course_class_id': assigned_course_class['course_class_id'],
                    'course_id': course['course_id'],  # Store course_id
                    'semester_id': course['semester_id'],  # Store semester_id
                    'credits': course['credits'],
                    'enrollment_date': course['semester_start'],
                    'status': status
                })
                
                # Log fixed student enrollments for debugging
                if is_fixed:
                    grade_status = "FULL GRADES" if final is not None else \
                                "ATT+MID" if midterm is not None else \
                                "ATT ONLY" if attendance is not None else "NO GRADES"
                    self.add_statement(f"-- ENROLLED: STUDENT (fixed) - {course['subject_code']} - {course['start_year']} {course['semester_type']} - {grade_status}")
        
        self.add_statement(f"\n-- ========================================")
        self.add_statement(f"-- ENROLLMENT SUMMARY")
        self.add_statement(f"-- ========================================")
        self.add_statement(f"-- Total enrollments created: {len(enrollment_rows)}")
        self.add_statement(f"-- Schedule conflicts detected: {conflict_count}")
        self.add_statement(f"-- Enrollments skipped (no conflict-free slot): {skipped_count}")
        
        # REMOVED is_paid column from insert
        self.bulk_insert('student_enrollment',
                        ['enrollment_id', 'student_id', 'course_class_id', 'enrollment_date',
                        'enrollment_status', 'cancellation_date', 'cancellation_reason',
                        'attendance_grade', 'midterm_grade', 'final_grade'],
                        enrollment_rows)

    def create_student_health_insurance(self):
        """
        UPDATED: Store insurance IDs for payment generation
        Now tracks insurance records that will be paid via payment_insurance table
        REMOVED: is_paid column (no longer in schema)
        """
        self.add_statement("\n-- ==================== STUDENT HEALTH INSURANCE ====================")
        
        insurance_rows = []
        insurance_fee = 500000  # 500,000 VND per year
        
        # IMPORTANT: Initialize insurances list
        self.data['insurances'] = []
        
        # Build academic year date lookup from semesters
        ay_dates = {}
        for semester in self.data['semesters']:
            ay_id = semester['academic_year_id']
            if ay_id not in ay_dates:
                ay_dates[ay_id] = {
                    'start_date': semester['start_date'],
                    'end_date': semester['end_date']
                }
            else:
                if semester['start_date'] < ay_dates[ay_id]['start_date']:
                    ay_dates[ay_id]['start_date'] = semester['start_date']
                if semester['end_date'] > ay_dates[ay_id]['end_date']:
                    ay_dates[ay_id]['end_date'] = semester['end_date']
        
        for student in self.data['students']:
            student_start_year = student['class_start_year']
            
            for ay in self.data['academic_years']:
                if ay['start_year'] >= student_start_year and ay['start_year'] <= 2025:
                    insurance_id = self.generate_uuid()
                    
                    dates = ay_dates.get(ay['academic_year_id'])
                    if not dates:
                        start_date = date(ay['start_year'], 9, 1)
                        end_date = date(ay['end_year'], 8, 31)
                    else:
                        start_date = dates['start_date']
                        end_date = dates['end_date']
                    
                    # Determine if this insurance should have a payment record
                    should_have_payment = (ay['start_year'] <= 2024)  # Only past years are paid
                    status = 'active' if ay['end_year'] >= 2025 else 'expired'
                    
                    insurance_rows.append([
                        insurance_id,
                        student['student_id'],
                        ay['academic_year_id'],
                        insurance_fee,
                        start_date,
                        end_date,
                        status
                    ])
                    
                    # STORE insurance data for payment generation
                    self.data['insurances'].append({
                        'insurance_id': insurance_id,
                        'student_id': student['student_id'],
                        'academic_year_id': ay['academic_year_id'],
                        'fee': insurance_fee,
                        'start_date': start_date,
                        'should_have_payment': should_have_payment  # Changed from is_paid
                    })
        
        self.add_statement(f"-- Total health insurance records: {len(insurance_rows)}")
        
        # REMOVED is_paid from column list
        self.bulk_insert('student_health_insurance',
                        ['insurance_id', 'student_id', 'academic_year_id', 'insurance_fee',
                        'start_date', 'end_date', 'insurance_status'],
                        insurance_rows)

    def create_payments(self):
        """
        UPDATED: Generate payments using NEW schema structure
        - payment_enrollment: for course tuition (with payment_enrollment_detail)
        - payment_insurance: for health insurance
        """
        self.add_statement("\n-- ==================== PAYMENTS ====================")
        self.add_statement("-- Creating payments in TWO separate tables:")
        self.add_statement("-- 1. payment_enrollment + payment_enrollment_detail (course tuition)")
        self.add_statement("-- 2. payment_insurance (health insurance)")
        
        enrollment_payment_rows = []
        enrollment_detail_rows = []
        insurance_payment_rows = []
        
        # =========================================================================
        # 1. COURSE TUITION PAYMENTS (payment_enrollment + payment_enrollment_detail)
        # =========================================================================
        self.add_statement("\n-- Generating course tuition payments...")
        
        # Group enrollments by student and semester
        enrollments_by_student_semester = defaultdict(list)
        for enrollment in self.data.get('enrollments', []):
            if enrollment.get('status') in ['completed', 'registered']:
                # Get course info to find semester
                course_class = next((cc for cc in self.data['course_classes'] 
                                if cc['course_class_id'] == enrollment['course_class_id']), None)
                if course_class:
                    key = (enrollment['student_id'], course_class['semester_id'])
                    enrollments_by_student_semester[key].append(enrollment)
        
        self.add_statement(f"-- Found {len(enrollments_by_student_semester)} unique student-semester combinations")
        
        # Create ONE payment_enrollment per student per semester
        for (student_id, semester_id), enrollments in enrollments_by_student_semester.items():
            payment_id = self.generate_uuid()
            
            # Calculate total amount for all courses in this semester
            total_amount = 0
            for enr in enrollments:
                course = next((c for c in self.data['courses'] 
                            if c['course_id'] == enr['course_id']), None)
                if course:
                    credits = course.get('credits', 0)
                    fee_per_credit = course.get('fee_per_credit', 600000)
                    total_amount += credits * fee_per_credit
            
            # Payment date: shortly after first enrollment date
            first_enrollment_date = min(e['enrollment_date'] for e in enrollments)
            payment_date = first_enrollment_date + timedelta(days=random.randint(1, 15))
            
            # Transaction reference (bank transfer code, etc.)
            transaction_ref = f"TXN{random.randint(100000000, 999999999)}"
            
            # Insert payment_enrollment
            enrollment_payment_rows.append([
                payment_id,
                student_id,
                semester_id,
                payment_date,
                total_amount,
                transaction_ref,
                'completed',
                f'Thanh toán học phí học kỳ'
            ])
            
            # Create payment_enrollment_detail for EACH enrollment
            for enr in enrollments:
                detail_id = self.generate_uuid()
                
                course = next((c for c in self.data['courses'] 
                            if c['course_id'] == enr['course_id']), None)
                
                if course:
                    credits = course.get('credits', 0)
                    fee_per_credit = course.get('fee_per_credit', 600000)
                    amount_paid = credits * fee_per_credit
                    
                    enrollment_detail_rows.append([
                        detail_id,
                        payment_id,
                        enr['enrollment_id'],
                        amount_paid
                    ])
        
        self.add_statement(f"-- Total payment_enrollment records: {len(enrollment_payment_rows)}")
        self.add_statement(f"-- Total payment_enrollment_detail records: {len(enrollment_detail_rows)}")
        
        # =========================================================================
        # 2. HEALTH INSURANCE PAYMENTS (payment_insurance)
        # =========================================================================
        self.add_statement("\n-- Generating health insurance payments...")
        
        for insurance in self.data.get('insurances', []):
            if insurance.get('should_have_payment', False):  # Changed from is_paid
                payment_id = self.generate_uuid()
                
                # Payment date: before start date
                payment_date = insurance['start_date'] - timedelta(days=random.randint(7, 30))
                
                insurance_payment_rows.append([
                    payment_id,
                    insurance['insurance_id'],
                    payment_date,
                    'Thanh toán bảo hiểm y tế sinh viên'
                ])
        
        self.add_statement(f"-- Total insurance payments: {len(insurance_payment_rows)}")
        
        # =========================================================================
        # INSERT INTO DATABASE
        # =========================================================================
        
        # Insert payment_enrollment (NO payment_method column!)
        self.bulk_insert('payment_enrollment',
                        ['payment_id', 'student_id', 'semester_id', 'payment_date', 
                        'total_amount', 'transaction_reference', 'payment_status', 'notes'],
                        enrollment_payment_rows)
        
        # Insert payment_enrollment_detail
        self.bulk_insert('payment_enrollment_detail',
                        ['payment_enrollment_detail_ID', 'payment_id', 'enrollment_id', 
                        'amount_paid'],
                        enrollment_detail_rows)
        
        # Insert payment_insurance
        self.bulk_insert('payment_insurance',
                        ['payment_id', 'insurance_id', 'payment_date', 'notes'],
                        insurance_payment_rows)


    def create_exam_schedules(self):
        self.add_statement("\n-- ==================== EXAMS ====================")
        self.add_statement("-- exam table references room_id directly (not room_booking)")
        
        exam_rows = []
        
        # Group courses by semester
        courses_by_semester = defaultdict(list)
        for course in self.data['courses']:
            courses_by_semester[course['semester_id']].append(course)
        
        for semester in self.data['semesters']:
            sem_id = semester['semester_id']
            if sem_id not in courses_by_semester:
                continue
            
            courses = courses_by_semester[sem_id]
            
            # Exam period: last 2 weeks
            sem_end = semester['end_date']
            exam_start = sem_end - timedelta(days=14)
            
            exam_dates = []
            current = exam_start
            while current <= sem_end:
                if current.weekday() < 6:  # Monday to Saturday
                    exam_dates.append(current)
                current += timedelta(days=1)
            
            if not exam_dates:
                continue
            
            exam_slots = [
                ('07:30:00', 120),  # 2 hours
                ('10:00:00', 120),
                ('13:30:00', 120),
                ('16:00:00', 120),
            ]
            
            # Track room usage: (room_id, date, start_time) -> True
            exam_room_usage = {}
            
            for course in courses:
                exam_format = random.choice(['multiple_choice', 'essay', 'practical', 'oral', 'mixed'])
                exam_type = random.choice(['midterm', 'final', 'final', 'final'])
                
                # Find course_classes for this course
                course_classes = [cc for cc in self.data['course_classes'] if cc['course_id'] == course['course_id']]
                
                for cc in course_classes:
                    exam_scheduled = False
                    for attempt in range(20):
                        exam_date = random.choice(exam_dates)
                        exam_time_start, duration = random.choice(exam_slots)
                        room = random.choice(self.data['rooms'])
                        
                        key = (room['room_id'], exam_date, exam_time_start)
                        if key not in exam_room_usage:
                            exam_room_usage[key] = True
                            
                            exam_id = self.generate_uuid()
                            notes = f"Thi {exam_type} - {course['subject_name']}"
                            
                            # exam table: course_class_id, room_id, exam_date, start_time, duration_minutes, 
                            # exam_format, exam_type, exam_file_path, answer_key_file_path, notes, exam_status
                            exam_rows.append([
                                exam_id,
                                cc['course_class_id'],
                                room['room_id'],  # Direct room_id reference
                                exam_date,
                                exam_time_start,
                                duration,
                                exam_format,
                                exam_type,
                                None,  # exam_file_path
                                None,  # answer_key_file_path
                                notes,
                                'scheduled'  # exam_status
                            ])
                            
                            exam_scheduled = True
                            break
                    
                    if not exam_scheduled:
                        # Fallback: schedule anyway (may have conflicts)
                        exam_date = random.choice(exam_dates)
                        exam_time_start, duration = random.choice(exam_slots)
                        room = random.choice(self.data['rooms'])
                        
                        exam_id = self.generate_uuid()
                        notes = f"Thi {exam_type} - {course['subject_name']}"
                        
                        exam_rows.append([
                            exam_id,
                            cc['course_class_id'],
                            room['room_id'],  # Direct room_id reference
                            exam_date,
                            exam_time_start,
                            duration,
                            exam_format,
                            exam_type,
                            None,  # exam_file_path
                            None,  # answer_key_file_path
                            notes,
                            'scheduled'  # exam_status
                        ])
        
        self.add_statement(f"-- Total exams: {len(exam_rows)}")
        
        # Insert into exam table (NO room_booking involved)
        self.bulk_insert('exam',
                        ['exam_id', 'course_class_id', 'room_id', 'exam_date', 'start_time', 'duration_minutes',
                        'exam_format', 'exam_type', 'exam_file_path', 'answer_key_file_path', 'notes', 'exam_status'],
                        exam_rows)

    def create_room_bookings(self):
        """
        Optional function to populate room_booking table for non-exam bookings
        (meetings, events, etc.) if needed
        """
        self.add_statement("\n-- ==================== ROOM BOOKINGS (OPTIONAL) ====================")
        self.add_statement("-- Creating sample room bookings for meetings and events")
        
        booking_rows = []
        
        # Get admin user for booking
        admin_user_id = self.data['fixed_accounts']['admin']['user_id']
        
        # Generate some random room bookings for demonstration
        booking_types = ['event', 'meeting', 'other']
        num_bookings = 20  # Create 20 sample bookings
        
        for i in range(num_bookings):
            booking_id = self.generate_uuid()
            room = random.choice(self.data['rooms'])
            booking_type = random.choice(booking_types)
            
            # Random date in 2025
            booking_date = date(2025, random.randint(1, 12), random.randint(1, 28))
            start_time = f"{random.randint(8, 16):02d}:00:00"
            end_time = f"{random.randint(10, 18):02d}:00:00"
            
            purpose = f"Sample {booking_type} booking #{i+1}"
            
            booking_rows.append([
                booking_id,
                room['room_id'],
                booking_type,
                booking_date,
                start_time,
                end_time,
                admin_user_id,
                purpose,
                'confirmed'  # booking_status
            ])
        
        self.add_statement(f"-- Total room bookings: {len(booking_rows)}")
        
        self.bulk_insert('room_booking',
                        ['booking_id', 'room_id', 'booking_type', 'booking_date', 'start_time', 'end_time',
                        'booked_by', 'purpose', 'booking_status'],
                        booking_rows)

    def create_schedule_changes(self):
        """
        NEW: Generate schedule change records (makeup classes, cancellations)
        """
        self.add_statement("\n-- ==================== SCHEDULE CHANGES ====================")
        
        schedule_change_rows = []
        
        # Create schedule changes for ~10% of course_classes
        sample_classes = random.sample(self.data['course_classes'], 
                                    min(len(self.data['course_classes']) // 10, 50))
        
        for cc in sample_classes:
            schedule_change_id = self.generate_uuid()
            
            # Random cancelled week and makeup week
            cancelled_week = random.randint(1, 12)
            makeup_week = random.randint(13, 16)
            
            # Makeup date
            makeup_date = cc['semester_start'] + timedelta(weeks=makeup_week)
            
            # Different room for makeup
            makeup_room = random.choice(self.data['rooms'])
            
            # Use original day/time or adjust
            day_of_week = cc['days'][0]  # Use first day
            
            schedule_change_rows.append([
                schedule_change_id,
                cc['course_class_id'],
                cancelled_week,
                makeup_week,
                makeup_date,
                makeup_room['room_id'],
                day_of_week,
                cc['start_period'],
                cc['end_period'],
                'Lý do hủy: Giảng viên bận công tác'
            ])
        
        self.add_statement(f"-- Total schedule changes: {len(schedule_change_rows)}")
        
        self.bulk_insert('schedule_change',
                        ['schedule_change_id', 'course_class_id', 'cancelled_week',
                        'makeup_week', 'makeup_date', 'makeup_room_id', 'day_of_week',
                        'start_period', 'end_period', 'reason'],
                        schedule_change_rows)


    def create_notifications(self):
        """
        NEW: Generate notification schedules
        """
        self.add_statement("\n-- ==================== NOTIFICATIONS ====================")
        
        notification_rows = []
        
        # Get admin user for creating notifications
        admin_user_id = self.data['fixed_accounts']['admin']['user_id']
        
        notification_types = ['event', 'tuition', 'schedule', 'important']
        target_types = ['all', 'all_students', 'all_instructors']
        
        # Create 20 sample notifications
        for i in range(20):
            schedule_id = self.generate_uuid()
            notif_type = random.choice(notification_types)
            target_type = random.choice(target_types)
            
            scheduled_date = datetime.now() - timedelta(days=random.randint(0, 90))
            visible_from = scheduled_date - timedelta(days=random.randint(1, 7))
            
            titles = {
                'event': f'Sự kiện: Hội thảo khoa học #{i+1}',
                'tuition': f'Thông báo: Đóng học phí kỳ {i+1}',
                'schedule': f'Thay đổi lịch học tuần {i+1}',
                'important': f'Thông báo quan trọng #{i+1}'
            }
            
            notification_rows.append([
                schedule_id,
                notif_type,
                titles.get(notif_type, 'Thông báo'),
                f'Nội dung thông báo số {i+1}',
                scheduled_date,
                visible_from,
                0,  # is_read
                target_type,
                None,  # target_id
                admin_user_id,
                'sent'
            ])
        
        self.add_statement(f"-- Total notifications: {len(notification_rows)}")
        
        self.bulk_insert('notification_schedule',
                        ['schedule_id', 'notification_type', 'title', 'content',
                        'scheduled_date', 'visible_from', 'is_read', 'target_type',
                        'target_id', 'created_by_user', 'status'],
                        notification_rows)
    
    def create_documents(self):
        """
        Generate document records for course materials
        Associates documents with course_classes and instructors
        """
        self.add_statement("\n-- ==================== COURSE DOCUMENTS ====================")
        self.add_statement("-- Generating course material documents (PDFs, images, Excel files)")
        
        document_rows = []
        
        # Get available document files from media scanner
        pdf_files = self.media_scanner.files['course_docs']['pdf']
        image_files = self.media_scanner.files['course_docs']['images']
        excel_files = self.media_scanner.files['course_docs']['excel']
        
        total_files = len(pdf_files) + len(image_files) + len(excel_files)
        
        if total_files == 0:
            self.add_statement("-- WARNING: No course document files found in medias/course_docs/")
            self.add_statement("-- Skipping document generation")
            return
        
        self.add_statement(f"-- Found {len(pdf_files)} PDFs, {len(image_files)} images, {len(excel_files)} Excel files")
        
        # Document type descriptions
        descriptions = {
            'pdf': [
                'Bài giảng lý thuyết',
                'Tài liệu tham khảo',
                'Đề cương môn học',
                'Slide bài giảng',
                'Tài liệu ôn tập'
            ],
            'image': [
                'Hình ảnh minh họa',
                'Sơ đồ tư duy',
                'Biểu đồ phân tích',
                'Ảnh thực hành'
            ],
            'excel': [
                'Bảng dữ liệu mẫu',
                'Điểm danh sinh viên',
                'Kết quả thực hành',
                'Bảng tính thống kê'
            ]
        }
        
        # File size ranges (in bytes)
        file_size_ranges = {
            'pdf': (100000, 5000000),
            'docx': (50000, 2000000),
            'doc': (50000, 2000000),
            'pptx': (500000, 10000000),
            'ppt': (500000, 10000000),
            'xlsx': (50000, 1000000),
            'xls': (50000, 1000000),
            'jpg': (100000, 5000000),
            'jpeg': (100000, 5000000),
            'png': (100000, 5000000),
            'zip': (1000000, 50000000),
            'rar': (1000000, 50000000)
        }
        
        # Generate documents for course_classes
        # Each course_class gets 2-5 documents
        for course_class in self.data['course_classes']:
            num_docs = random.randint(2, 5)
            
            for i in range(num_docs):
                document_id = self.generate_uuid()
                
                # Randomly select document type and file
                doc_type = random.choice(['pdf', 'image', 'excel'])
                
                if doc_type == 'pdf' and pdf_files:
                    file_name = random.choice(pdf_files)
                    file_type = 'pdf'
                    desc_pool = descriptions['pdf']
                elif doc_type == 'image' and image_files:
                    file_name = random.choice(image_files)
                    file_ext = file_name.split('.')[-1].lower()
                    file_type = file_ext if file_ext in ['jpg', 'jpeg', 'png'] else 'jpg'
                    desc_pool = descriptions['image']
                elif doc_type == 'excel' and excel_files:
                    file_name = random.choice(excel_files)
                    file_ext = file_name.split('.')[-1].lower()
                    file_type = file_ext if file_ext in ['xlsx', 'xls'] else 'xlsx'
                    desc_pool = descriptions['excel']
                else:
                    # Fallback to PDF if preferred type not available
                    if pdf_files:
                        file_name = random.choice(pdf_files)
                        file_type = 'pdf'
                        desc_pool = descriptions['pdf']
                    else:
                        continue
                
                # Build file path URL using correct bucket
                file_path = self.media_scanner.build_url('instructor_documents', file_name)
                
                # Generate file size
                size_min, size_max = file_size_ranges.get(file_type, (100000, 5000000))
                file_size = random.randint(size_min, size_max)
                
                # Random description
                description = random.choice(desc_pool)
                
                # Uploaded by instructor
                uploaded_by = course_class.get('instructor_id')
                
                document_rows.append([
                    document_id,
                    course_class['course_class_id'],
                    file_name,
                    file_path,
                    file_type,
                    file_size,
                    uploaded_by,
                    description
                ])
        
        self.add_statement(f"-- Total documents generated: {len(document_rows)}")
        
        self.bulk_insert('document',
                        ['document_id', 'course_class_id', 'file_name', 'file_path',
                        'file_type', 'file_size', 'uploaded_by', 'description'],
                        document_rows)
        
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

    # ==================== MAIN GENERATION ====================
    def generate_all(self):
        """
        UPDATED: Main generation with new functions
        """
        print("Generating SQL data from spec file...")
        
        self.add_statement("-- ============================================================")
        self.add_statement("-- EDUMANAGEMENT DATABASE - COMPLETE SCHEMA GENERATION")
        self.add_statement(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_statement(f"-- Spec file: {self.spec_file}")
        self.add_statement("-- UPDATED FOR COMPLETE NEW SCHEMA")
        self.add_statement("-- ============================================================")
        self.add_statement("USE EduManagement;")
        self.add_statement("GO\n")
        
        # Core entities
        self.create_permissions()
        self.create_fixed_test_accounts()
        self.create_regular_staff()
        self.create_faculties_and_departments()
        self.create_academic_years_and_semesters()
        self.create_buildings_and_rooms()
        self.create_room_amenities()
        self.create_room_amenity_mappings()
        
        # Academic structure
        self.create_classes()
        self.create_subjects()
        self.map_class_curricula()
        self.create_curriculum_details()  # UPDATED
        self.create_students()
        
        # Course management
        self.create_courses()
        self.create_course_classes()
        self.create_student_enrollments()
        self.create_documents() 
        
        # Exams and assessments
        self.create_exams_and_exam_classes()  # NEW/UPDATED
        
        # Additional features
        self.create_student_health_insurance()  # NEW
        self.create_payments()  # NEW
        self.create_schedule_changes()  # NEW
        self.create_notifications()  # NEW

        # Regulations
        self.create_regulations()
        
        self.add_statement("\n-- ============================================================")
        self.add_statement("-- GENERATION COMPLETE - STATISTICS")
        self.add_statement("-- ============================================================")
        self.add_statement(f"-- Students: {len(self.data['students'])}")
        self.add_statement(f"-- Instructors: {len(self.data['instructors'])}")
        self.add_statement(f"-- Courses: {len(self.data['courses'])}")
        self.add_statement(f"-- Course Classes: {len(self.data['course_classes'])}")
        self.add_statement(f"-- Buildings: {len(self.data['buildings'])}")
        self.add_statement(f"-- Rooms: {len(self.data['rooms'])}")
        self.add_statement(f"-- Regulations: {len(self.data['regulations'])}")
        
        return '\n'.join(self.sql_statements)

# ==================== RUN ====================
if __name__ == "__main__":
    import sys
    
    # Use command line arg or default SPEC_FILE
    spec_file = sys.argv[1] if len(sys.argv) > 1 else SPEC_FILE
    
    if not os.path.exists(spec_file):
        print(f"Error: Spec file not found: {spec_file}")
        print(f"Usage: python generate_data.py [spec_file]")
        print(f"Default spec file: {SPEC_FILE}")
        sys.exit(1)
    
    print("="*70)
    print("EDUMANAGEMENT SQL DATA GENERATOR (UPDATED SCHEMA)")
    print("="*70)
    print(f"Using spec file: {spec_file}")
    print("="*70)
    print("\nChanges in this version:")
    print("- Removed room_booking table generation")
    print("- exam_schedule now references room_id directly")
    print("- All other functionality remains the same")
    print("="*70)
    
    generator = SQLDataGenerator(spec_file)
    output_file = generator.save_to_file()
    
    print("\n" + "="*70)
    print("READY TO EXECUTE!")
    print("="*70)
    print("\nNext steps:")
    print("1. Review the generated SQL file")
    print("2. Execute against your database")
    print("3. Verify data integrity")
    print("="*70)