"""
EduManagement SQL Data Generator - Spec-Driven (UPDATED SCHEMA)
===============================================
Reads configuration from spec file and generates REALISTIC, MASSIVE data
Includes proper course_class scheduling and student enrollments
UPDATED: Removed room_booking, exam_schedule now references room directly
"""

# ==================== CONFIGURATION ====================
SPEC_FILE = 'school/uni/specs.txt'
OUTPUT_FILE = 'school/uni/insert_data.sql'
# ========================================================

import uuid
import random
import os
import hmac
import hashlib
import base64
from datetime import datetime, date, timedelta
from collections import defaultdict

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
                elif self.current_section and ':' in line:
                    key, value = line.split(':', 1)
                    self.data.setdefault(self.current_section + '_config', {})[key.strip()] = value.strip()
                elif self.current_section and '|' in line:
                    self.data[self.current_section].append(line)
        
        return self.data

class SQLDataGenerator:
    def __init__(self, spec_file):
        self.spec_file = spec_file
        self.spec_data = SpecParser(spec_file).parse()
        self.sql_statements = []
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
            'course_classes': [],
            'fixed_accounts': {}
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
        
        self.bulk_insert('permissions', ['permission_id', 'role_name', 'permission_name', 'description'], rows)
    
    # ==================== FIXED TEST ACCOUNTS ====================
    def create_fixed_test_accounts(self):
        self.add_statement("\n-- ==================== FIXED TEST ACCOUNTS ====================")
        
        password = self.test_config.get('password', '123456')
        salt_b64 = self.test_config.get('salt_base64', 'MTExMQ==')
        salt_bytes = base64.b64decode(salt_b64)
        password_hash = self.create_password_hash(password, salt_bytes)
        
        self.add_statement(f"-- Password: {password}")
        self.add_statement(f"-- Salt: {salt_b64}")
        self.add_statement(f"-- Hash: {password_hash}")
        
        person_rows = []
        user_rows = []
        instructor_rows = []
        admin_rows = []
        
        # INSTRUCTOR
        person_id = self.generate_uuid()
        user_id = self.generate_uuid()
        instructor_id = self.generate_uuid()
        
        self.data['fixed_accounts']['instructor'] = {
            'person_id': person_id,
            'user_id': user_id,
            'instructor_id': instructor_id,
            'full_name': self.test_config.get('instructor_name', 'Test Instructor')
        }
        
        # Generate 12-digit citizen_id
        instructor_citizen_id = f"{random.randint(100000000000, 999999999999)}"
        
        person_rows.append([person_id, self.test_config.get('instructor_name'), 
                        self.test_config.get('instructor_dob', '1985-01-01'),
                        self.test_config.get('instructor_gender', 'female'),
                        self.test_config.get('instructor_email'),
                        self.test_config.get('instructor_phone'),
                        instructor_citizen_id,
                        'TP Hồ Chí Minh'])
        
        user_rows.append([user_id, person_id, self.test_config.get('instructor_username'),
                        password_hash, salt_b64, 'Instructor', 'active'])
        
        instructor_rows.append([instructor_id, person_id, self.test_config.get('instructor_code'),
                            self.test_config.get('instructor_degree'), 
                            self.test_config.get('instructor_hire_date'), 'active'])
        
        self.data['instructors'].append({'instructor_id': instructor_id, 'person_id': person_id,
                                        'full_name': self.test_config.get('instructor_name')})
        
        # ADMIN
        person_id = self.generate_uuid()
        user_id = self.generate_uuid()
        admin_id = self.generate_uuid()
        
        self.data['fixed_accounts']['admin'] = {'person_id': person_id, 'user_id': user_id, 'admin_id': admin_id}
        
        # Generate 12-digit citizen_id
        admin_citizen_id = f"{random.randint(100000000000, 999999999999)}"
        
        person_rows.append([person_id, self.test_config.get('admin_name'),
                        self.test_config.get('admin_dob'),
                        self.test_config.get('admin_gender'),
                        self.test_config.get('admin_email'),
                        self.test_config.get('admin_phone'),
                        admin_citizen_id,
                        'TP Hồ Chí Minh'])
        
        user_rows.append([user_id, person_id, self.test_config.get('admin_username'),
                        password_hash, salt_b64, 'Admin', 'active'])
        
        admin_rows.append([admin_id, person_id, self.test_config.get('admin_code'),
                        self.test_config.get('admin_position'), 'active'])
        
        self.data['admins'].append({'admin_id': admin_id, 'person_id': person_id})
        
        self.bulk_insert('person', ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 'phone_number', 'citizen_id', 'address'], person_rows)
        self.bulk_insert('user_account', ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 'role_name', 'status'], user_rows)
        self.bulk_insert('instructor', ['instructor_id', 'person_id', 'instructor_code', 'degree', 'hire_date', 'status'], instructor_rows)
        self.bulk_insert('admin', ['admin_id', 'person_id', 'admin_code', 'position', 'status'], admin_rows)

    # ==================== REGULAR STAFF ====================
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
            
            # Generate 12-digit citizen_id
            citizen_id = f"{random.randint(100000000000, 999999999999)}"
            
            person_rows.append([person_id, full_name, dob, gender, email, phone, citizen_id, 'TP Hồ Chí Minh'])
            
            user_id = self.generate_uuid()
            username = f"gv{i+1:02d}"
            user_rows.append([user_id, person_id, username, 'hashed_pwd', 'salt', 'Instructor', 'active'])
            
            instructor_id = self.generate_uuid()
            degree = random.choice(['Tiến sĩ', 'Thạc sĩ', 'Cử nhân'])
            hire_date = date(random.randint(2010, 2020), random.randint(1, 12), 1)
            instructor_rows.append([instructor_id, person_id, f"GV{i+1:04d}", degree, hire_date, 'active'])
            
            self.data['instructors'].append({'instructor_id': instructor_id, 'person_id': person_id, 'full_name': full_name})
        
        # Admins
        num_admins = int(self.staff_config.get('regular_admins', 2))
        for i in range(num_admins):
            person_id = self.generate_uuid()
            full_name = f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_names_male)}"
            email = f"admin{i+1}@edu.vn"
            phone = f"0{random.randint(300000000, 999999999)}"
            
            # Generate 12-digit citizen_id
            citizen_id = f"{random.randint(100000000000, 999999999999)}"
            
            person_rows.append([person_id, full_name, date(1975, 1, 1), 'male', email, phone, citizen_id, 'TP Hồ Chí Minh'])
            
            user_id = self.generate_uuid()
            username = f"admin{i+1}"
            user_rows.append([user_id, person_id, username, 'hashed_pwd', 'salt', 'Admin', 'active'])
            
            admin_id = self.generate_uuid()
            admin_rows.append([admin_id, person_id, f"AD{i+1:04d}", 'Quản trị viên', 'active'])
            
            self.data['admins'].append({'admin_id': admin_id, 'person_id': person_id})
        
        self.bulk_insert('person', ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 'phone_number', 'citizen_id', 'address'], person_rows)
        self.bulk_insert('user_account', ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 'role_name', 'status'], user_rows)
        self.bulk_insert('instructor', ['instructor_id', 'person_id', 'instructor_code', 'degree', 'hire_date', 'status'], instructor_rows)
        self.bulk_insert('admin', ['admin_id', 'person_id', 'admin_code', 'position', 'status'], admin_rows)

    # ==================== FACULTIES & DEPARTMENTS ====================
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
                department_rows.append([dept_id, dept_name, dept_code, faculty_id, head_id])
        
        self.bulk_insert('faculty', ['faculty_id', 'faculty_name', 'faculty_code', 'dean_id', 'status'], faculty_rows)
        self.bulk_insert('department', ['department_id', 'department_name', 'department_code', 'faculty_id', 'head_of_department_id'], department_rows)
    
    # ==================== ACADEMIC YEARS & SEMESTERS ====================
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
            
            ay_rows.append([academic_year_id, start_date, end_date, status])
            
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
                
                sem_rows.append([semester_id, sem_name, academic_year_id, sem_type, sem_start, sem_end, reg_start, reg_end, 'active'])
        
        self.bulk_insert('academic_year', ['academic_year_id', 'start_date', 'end_date', 'status'], ay_rows)
        self.bulk_insert('semester', ['semester_id', 'semester_name', 'academic_year_id', 'semester_type', 'start_date', 'end_date', 'registration_start_date', 'registration_end_date', 'status'], sem_rows)

    # ==================== CLASSES ====================
    def create_classes(self):
        self.add_statement("\n-- ==================== CLASSES ====================")
        
        class_rows = []
        class_names = set()
        
        for line in self.spec_data.get('class_curricula', []):
            parts = [p.strip() for p in line.split('|')]
            class_name = parts[0]
            
            if class_name in class_names:
                continue
            class_names.add(class_name)
            
            # Extract year from class name (e.g., K2023-1 -> 2023)
            year = int(class_name[1:5])
            
            # Find matching academic year
            matching_ay = next((ay for ay in self.data['academic_years'] if ay['start_year'] == year), None)
            if not matching_ay:
                continue
            
            class_id = self.generate_uuid()
            class_code = class_name
            
            self.data['classes'].append({
                'class_id': class_id,
                'class_code': class_code,
                'class_name': class_name,
                'start_academic_year_id': matching_ay['academic_year_id'],
                'start_year': year,
                'department_name': parts[1]
            })
            
            class_rows.append([class_id, class_code, class_name, matching_ay['academic_year_id']])
        
        self.bulk_insert('class', ['class_id', 'class_code', 'class_name', 'start_academic_year_id'], class_rows)
    
    # ==================== SUBJECTS ====================
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
            
            subject_rows.append([subject_id, subj_name, subj_code, int(credits), int(theory), int(practice), True, default_dept_id, 'active'])
        
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
            
            subject_rows.append([subject_id, subj_name, subj_code, int(credits), int(theory), int(practice), False, dept['department_id'], 'active'])
        
        self.bulk_insert('subject', ['subject_id', 'subject_name', 'subject_code', 'credits', 'theory_hours', 'practice_hours', 'is_general', 'department_id', 'status'], subject_rows)
    
    def create_curriculum_details(self):
        self.add_statement("\n-- ==================== CURRICULUM DETAILS ====================")
        
        curriculum_rows = []
        
        for cls in self.data['classes']:
            if 'curriculum' not in cls or not cls['curriculum']:
                continue
            
            # Get semesters for this class's academic years
            class_start_year = cls['start_year']
            
            # Map subjects to appropriate semesters based on typical curriculum progression
            subjects = cls['curriculum']
            
            # Distribute subjects across semesters (roughly 4-6 subjects per semester)
            subjects_per_semester = 5
            semester_index = 0
            
            for i, subject in enumerate(subjects):
                # Find appropriate semester for this subject
                # Cycle through fall, spring, summer across years
                year_offset = semester_index // 3
                semester_type_index = semester_index % 3
                semester_types = ['fall', 'spring', 'summer']
                target_sem_type = semester_types[semester_type_index]
                target_year = class_start_year + year_offset
                
                # Find matching semester
                matching_sem = next(
                    (s for s in self.data['semesters'] 
                    if s['start_year'] == target_year and s['semester_type'] == target_sem_type),
                    None
                )
                
                if matching_sem:
                    curriculum_detail_id = self.generate_uuid()
                    curriculum_rows.append([
                        curriculum_detail_id,
                        cls['class_id'],
                        subject['subject_id'],
                        matching_sem['semester_id']
                    ])
                
                # Move to next semester after distributing subjects
                if (i + 1) % subjects_per_semester == 0:
                    semester_index += 1
        
        self.add_statement(f"-- Total curriculum details: {len(curriculum_rows)}")
        self.bulk_insert('curriculum_detail',
                        ['curriculum_detail_id', 'class_id', 'subject_id', 'semester_id'],
                        curriculum_rows)

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
    
    # ==================== STUDENTS ====================
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
        
        # Fixed STUDENT account
        password = self.test_config.get('password')
        salt_b64 = self.test_config.get('salt_base64')
        salt_bytes = base64.b64decode(salt_b64)
        password_hash = self.create_password_hash(password, salt_bytes)
        
        target_class_year = int(self.test_config.get('student_class_year', 2023))
        target_class = next((c for c in self.data['classes'] if c['start_year'] == target_class_year), None)
        
        if target_class:
            person_id = self.generate_uuid()
            user_id = self.generate_uuid()
            student_id = self.generate_uuid()
            
            self.data['fixed_accounts']['student'] = {
                'person_id': person_id,
                'user_id': user_id,
                'student_id': student_id,
                'class_id': target_class['class_id'],
                'class_start_year': target_class_year
            }
            
            # Generate 12-digit citizen_id for fixed student
            fixed_student_citizen_id = f"{random.randint(100000000000, 999999999999)}"
            
            person_rows.append([person_id, self.test_config.get('student_name'),
                            self.test_config.get('student_dob'),
                            self.test_config.get('student_gender'),
                            self.test_config.get('student_email'),
                            self.test_config.get('student_phone'),
                            fixed_student_citizen_id,
                            'TP Hồ Chí Minh'])
            
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
                
                # Generate 12-digit citizen_id
                citizen_id = f"{random.randint(100000000000, 999999999999)}"
                
                person_rows.append([person_id, full_name, dob, gender, email, phone, citizen_id, 'TP Hồ Chí Minh'])
                
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
        
        self.bulk_insert('person', ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 'phone_number', 'citizen_id', 'address'], person_rows)
        self.bulk_insert('user_account', ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 'role_name', 'status'], user_rows)
        self.bulk_insert('student', ['student_id', 'person_id', 'student_code', 'class_id', 'status'], student_rows)

    # ==================== BUILDINGS & ROOMS ====================
    def create_buildings_and_rooms(self):
        self.add_statement("\n-- ==================== BUILDINGS & ROOMS ====================")
        
        building_rows = []
        room_rows = []
        room_types = ['lecture_hall', 'classroom', 'computer_lab', 'laboratory']
        capacities = [30, 40, 50, 60]
        
        for line in self.spec_data.get('buildings', []):
            parts = [p.strip() for p in line.split('|')]
            bldg_name, bldg_code, rooms_count = parts[0], parts[1], int(parts[2])
            
            building_id = self.generate_uuid()
            self.data['buildings'].append({'building_id': building_id, 'building_name': bldg_name})
            building_rows.append([building_id, bldg_name, bldg_code, 'TP Hồ Chí Minh', 'active'])
            
            bldg_letter = bldg_code[-1]
            for j in range(rooms_count):
                room_id = self.generate_uuid()
                room_code = f"{bldg_letter}{j+1:02d}"
                room_name = f"Phòng {room_code}"
                capacity = random.choice(capacities)
                room_type = random.choice(room_types)
                
                self.data['rooms'].append({'room_id': room_id, 'room_code': room_code, 'capacity': capacity})
                room_rows.append([room_id, room_code, room_name, capacity, room_type, building_id, 'active'])
        
        self.bulk_insert('building', ['building_id', 'building_name', 'building_code', 'address', 'status'], building_rows)
        self.bulk_insert('room', ['room_id', 'room_code', 'room_name', 'capacity', 'room_type', 'building_id', 'status'], room_rows)
    
    # ==================== COURSES ====================
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
                
                # Use fixed instructor sometimes in fall 2025
                if semester['start_year'] == 2025 and sem_type == 'fall' and random.random() < 0.3:
                    instructor_id = self.data['fixed_accounts']['instructor']['instructor_id']
                else:
                    instructor_id = random.choice(self.data['instructors'])['instructor_id']
                
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
                    'semester_type': semester['semester_type'],
                    'instructor_id': instructor_id
                })
                
                course_rows.append([course_id, subject['subject_id'], instructor_id, semester['semester_id'], fee, 'active'])
        
        self.add_statement(f"-- Total courses generated: {len(course_rows)}")
        self.bulk_insert('course', ['course_id', 'subject_id', 'instructor_id', 'semester_id', 'fee_per_credit', 'status'], course_rows)
    
    # ==================== COURSE CLASSES (Multiple sessions per course) ====================
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
                            'room_id': room['room_id'],
                            'days': days,
                            'start_period': time_slot[0],
                            'end_period': time_slot[1],
                            'max_students': max_per_session,
                            'session_number': session_idx + 1,
                            'enrolled_count': 0  # Will be updated during enrollment
                        })
                        
                        # Insert ONE record with PRIMARY day (first day)
                        course_class_rows.append([
                            course_class_id,
                            course['course_id'],
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
                        'room_id': room['room_id'],
                        'days': days,
                        'start_period': time_slot[0],
                        'end_period': time_slot[1],
                        'max_students': max_per_session,
                        'session_number': session_idx + 1,
                        'enrolled_count': 0
                    })
                    
                    # Insert ONE record
                    course_class_rows.append([
                        course_class_id,
                        course['course_id'],
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
        self.bulk_insert('course_class', 
                        ['course_class_id', 'course_id', 'room_id', 'date_start', 'date_end', 
                        'max_students', 'day_of_week', 'start_period', 'end_period', 'status'],
                        course_class_rows)

    # ==================== STUDENT ENROLLMENTS (MASSIVE DATA WITH CONFLICT CHECKING) ====================
    def create_student_enrollments(self):
        self.add_statement("\n-- ==================== STUDENT COURSE ENROLLMENTS (REALISTIC & MASSIVE) ====================")
        self.add_statement("-- Students enrolled with STRICT schedule conflict checking")
        self.add_statement("-- Fixed STUDENT account gets deterministic grades for testing")
        
        enrollment_rows = []
        
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
                    attendance,
                    midterm,
                    final,
                    1  # is_paid
                ])
                
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
        
        self.bulk_insert('class_course_student',
                        ['enrollment_id', 'student_id', 'course_class_id', 'enrollment_date',
                        'status', 'attendance_grade', 'midterm_grade', 'final_grade', 'is_paid'],
                        enrollment_rows)

    # ==================== EXAM SCHEDULES WITH ROOM BOOKINGS ====================
    def create_exam_schedules(self):
        self.add_statement("\n-- ==================== ROOM BOOKINGS & EXAM SCHEDULES ====================")
        
        booking_rows = []
        exam_rows = []
        
        # Get admin user for booking
        admin_user_id = self.data['fixed_accounts']['admin']['user_id']
        
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
                ('07:30:00', '09:30:00'),
                ('10:00:00', '12:00:00'),
                ('13:30:00', '15:30:00'),
                ('16:00:00', '18:00:00'),
            ]
            
            # Track room usage: (room_id, date, start_time) -> True
            exam_room_usage = {}
            
            for course in courses:
                exam_format = random.choice(['multiple_choice', 'essay', 'practical', 'oral'])
                exam_type = random.choice(['midterm', 'final', 'final', 'final'])
                
                # Find course_classes for this course
                course_classes = [cc for cc in self.data['course_classes'] if cc['course_id'] == course['course_id']]
                
                for cc in course_classes:
                    exam_scheduled = False
                    for attempt in range(20):
                        exam_date = random.choice(exam_dates)
                        exam_time = random.choice(exam_slots)
                        room = random.choice(self.data['rooms'])
                        
                        key = (room['room_id'], exam_date, exam_time[0])
                        if key not in exam_room_usage:
                            exam_room_usage[key] = True
                            
                            # Create room_booking first
                            booking_id = self.generate_uuid()
                            booking_rows.append([
                                booking_id,
                                room['room_id'],
                                'exam',
                                exam_date,
                                exam_time[0],
                                exam_time[1],
                                admin_user_id,
                                f"Thi {exam_type} - {course['subject_name']}",
                                'confirmed'
                            ])
                            
                            # Create exam_schedule referencing the booking
                            exam_id = self.generate_uuid()
                            notes = f"Thi {exam_type} - {course['subject_name']}"
                            
                            exam_rows.append([
                                exam_id,
                                cc['course_class_id'],
                                booking_id,  # Reference to room_booking
                                exam_date,
                                exam_time[0],
                                exam_time[1],
                                exam_format,
                                exam_type,
                                notes
                            ])
                            
                            exam_scheduled = True
                            break
                    
                    if not exam_scheduled:
                        # Fallback: schedule anyway (may have conflicts)
                        exam_date = random.choice(exam_dates)
                        exam_time = random.choice(exam_slots)
                        room = random.choice(self.data['rooms'])
                        
                        # Create room_booking
                        booking_id = self.generate_uuid()
                        booking_rows.append([
                            booking_id,
                            room['room_id'],
                            'exam',
                            exam_date,
                            exam_time[0],
                            exam_time[1],
                            admin_user_id,
                            f"Thi {exam_type} - {course['subject_name']}",
                            'confirmed'
                        ])
                        
                        # Create exam_schedule
                        exam_id = self.generate_uuid()
                        notes = f"Thi {exam_type} - {course['subject_name']}"
                        
                        exam_rows.append([
                            exam_id,
                            cc['course_class_id'],
                            booking_id,  # Reference to room_booking
                            exam_date,
                            exam_time[0],
                            exam_time[1],
                            exam_format,
                            exam_type,
                            notes
                        ])
        
        self.add_statement(f"-- Total room bookings: {len(booking_rows)}")
        self.add_statement(f"-- Total exam schedules: {len(exam_rows)}")
        
        # Insert room_booking first (exam_schedule depends on it)
        self.bulk_insert('room_booking',
                        ['booking_id', 'room_id', 'booking_type', 'booking_date', 'start_time', 'end_time',
                        'booked_by', 'purpose', 'status'],
                        booking_rows)
        
        # Then insert exam_schedule
        self.bulk_insert('exam_schedule',
                        ['exam_id', 'course_class_id', 'room_booking_id', 'exam_date', 'start_time', 'end_time',
                        'exam_format', 'exam_type', 'notes'],
                        exam_rows)
    
    # ==================== MAIN GENERATION ====================
    def generate_all(self):
        print("Generating SQL data from spec file...")
        
        self.add_statement("-- ============================================================")
        self.add_statement("-- EDUMANAGEMENT DATABASE - SPEC-DRIVEN GENERATION")
        self.add_statement(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.add_statement(f"-- Spec file: {self.spec_file}")
        self.add_statement("-- CORRECT SCHEMA: exam_schedule references room_id directly")
        self.add_statement("-- ============================================================")
        self.add_statement("USE EduManagement;")
        self.add_statement("GO\n")
        
        self.create_permissions()
        self.create_fixed_test_accounts()
        self.create_regular_staff()
        self.create_faculties_and_departments()
        self.create_academic_years_and_semesters()
        self.create_classes()
        self.create_subjects()
        self.map_class_curricula()
        self.create_curriculum_details()  # ADD THIS LINE
        self.create_buildings_and_rooms()
        self.create_students()
        self.create_courses()
        self.create_course_classes()
        self.create_student_enrollments()
        self.create_exam_schedules()
        
        self.add_statement("\n-- ============================================================")
        self.add_statement("-- GENERATION COMPLETE - STATISTICS")
        self.add_statement("-- ============================================================")
        self.add_statement(f"-- Students: {len(self.data['students'])}")
        self.add_statement(f"-- Instructors: {len(self.data['instructors'])}")
        self.add_statement(f"-- Courses: {len(self.data['courses'])}")
        self.add_statement(f"-- Course Classes: {len(self.data['course_classes'])}")
        self.add_statement(f"-- Buildings: {len(self.data['buildings'])}")
        self.add_statement(f"-- Rooms: {len(self.data['rooms'])}")
        
        return '\n'.join(self.sql_statements)

    def save_to_file(self):
        sql_content = self.generate_all()
        
        output_file = OUTPUT_FILE
        directory = os.path.dirname(output_file)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        
        print(f"\n{'='*70}")
        print(f"SQL file generated: {output_file}")
        print(f"Total SQL statements: {len(self.sql_statements)}")
        print(f"File size: {len(sql_content):,} characters")
        print(f"{'='*70}")
        
        return output_file

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