import random
import base64
from datetime import date
from .config import *

def create_fixed_test_accounts(self):
    self.add_statement("\n-- ==================== FIXED TEST ACCOUNTS ====================")
    
    # Password configuration
    password = self.spec_data.get('test_accounts_config', {}).get('password', '123456')
    salt_b64 = self.spec_data.get('test_accounts_config', {}).get('salt_base64', 'MTExMQ==')
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
    
    # Get role IDs
    student_role_id = self.role_id_map.get('Student')
    instructor_role_id = self.role_id_map.get('Instructor')
    
    # ============================================================
    # STUDENT ACCOUNTS (AUTO-DETECT ALL test_student* sections)
    # ============================================================
    for config_key in self.spec_data.keys():
        if config_key.startswith('test_student') and config_key.endswith('_config'):
            student_config = self.spec_data.get(config_key, {})
            person_id = student_config.get('person_id')
            user_id = student_config.get('user_id')
            student_id = student_config.get('student_id')
            
            profile_pic = self.media_scanner.get_random_file('profile_pics')
            profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
            
            person_rows.append([
                person_id, 
                student_config.get('full_name'),
                student_config.get('date_of_birth'),
                student_config.get('gender'),
                student_config.get('email'),
                student_config.get('phone_number'),
                student_config.get('citizen_id'),
                student_config.get('address', 'TP Hồ Chí Minh'),
                profile_pic_url
            ])
            
            user_rows.append([
                user_id, 
                person_id, 
                student_config.get('username'),
                password_hash, 
                salt_b64, 
                student_role_id,
                'student',
                'active'
            ])
            
            # Store for later
            account_name = config_key.replace('_config', '').replace('test_', '')
            self.data['fixed_accounts'][account_name] = {
                'person_id': person_id,
                'user_id': user_id,
                'student_id': student_id,
                'class_id': None
            }
            
            self.add_statement(f"-- STUDENT ({account_name}): person={person_id}, user={user_id}, student={student_id}")
    
    # ============================================================
    # INSTRUCTOR ACCOUNTS (AUTO-DETECT ALL test_instructor* sections)
    # ============================================================
    for config_key in self.spec_data.keys():
        if config_key.startswith('test_instructor') and config_key.endswith('_config') and 'admin' not in config_key:
            instructor_config = self.spec_data.get(config_key, {})
            person_id = instructor_config.get('person_id')
            user_id = instructor_config.get('user_id')
            instructor_id = instructor_config.get('instructor_id')
            
            profile_pic = self.media_scanner.get_random_file('profile_pics')
            profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
            
            person_rows.append([
                person_id, 
                instructor_config.get('full_name'),
                instructor_config.get('date_of_birth'),
                instructor_config.get('gender'),
                instructor_config.get('email'),
                instructor_config.get('phone_number'),
                instructor_config.get('citizen_id'),
                instructor_config.get('address', 'TP Hồ Chí Minh'),
                profile_pic_url
            ])
            
            user_rows.append([
                user_id, 
                person_id, 
                instructor_config.get('username'),
                password_hash, 
                salt_b64, 
                instructor_role_id,
                'instructor',
                'active'
            ])
            
            instructor_rows.append([
                instructor_id, 
                person_id, 
                instructor_config.get('instructor_code'),
                instructor_config.get('degree'), 
                instructor_config.get('specialization'),
                None,
                instructor_config.get('hire_date'), 
                'active'
            ])
            
            self.data['instructors'].append({
                'instructor_id': instructor_id, 
                'person_id': person_id,
                'full_name': instructor_config.get('full_name')
            })
            
            account_name = config_key.replace('_config', '').replace('test_', '')
            self.data['fixed_accounts'][account_name] = {
                'person_id': person_id,
                'user_id': user_id,
                'instructor_id': instructor_id,
                'full_name': instructor_config.get('full_name')
            }
            
            self.add_statement(f"-- INSTRUCTOR ({account_name}): person={person_id}, user={user_id}, instructor={instructor_id}")
    
    # ============================================================
    # ADMIN ACCOUNTS (AUTO-DETECT ALL test_admin* sections)
    # ============================================================
    for config_key in self.spec_data.keys():
        if config_key.startswith('test_admin') and config_key.endswith('_config'):
            admin_config = self.spec_data.get(config_key, {})
            person_id = admin_config.get('person_id')
            user_id = admin_config.get('user_id')
            admin_id = admin_config.get('admin_id')
            
            # Determine role based on config key name
            if 'principal' in config_key:
                role_name = 'Admin_Principal'
                admin_type = 'principal'
            elif 'accountant' in config_key:
                role_name = 'Admin_Accountant'
                admin_type = 'accountant'
            elif 'academic' in config_key:
                role_name = 'Admin_Academic'
                admin_type = 'academic'
            elif 'hr' in config_key:
                role_name = 'Admin_HR'
                admin_type = 'hr'
            elif 'facilities' in config_key:
                role_name = 'Admin_Facilities'
                admin_type = 'facilities'
            else:
                # Generic admin account
                role_name = 'Admin'
                admin_type = 'admin'
            
            role_id = self.role_id_map.get(role_name)
            
            profile_pic = self.media_scanner.get_random_file('profile_pics')
            profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
            
            person_rows.append([
                person_id,
                admin_config.get('full_name'),
                admin_config.get('date_of_birth'),
                admin_config.get('gender'),
                admin_config.get('email'),
                admin_config.get('phone_number'),
                admin_config.get('citizen_id'),
                admin_config.get('address', 'TP Hồ Chí Minh'),
                profile_pic_url
            ])
            
            user_rows.append([
                user_id, 
                person_id, 
                admin_config.get('username'),
                password_hash, 
                salt_b64, 
                role_id,
                'admin',
                'active'
            ])
            
            admin_rows.append([
                admin_id, 
                person_id, 
                admin_config.get('admin_code'), 
                admin_config.get('position'), 
                'active'
            ])
            
            self.data['admins'].append({
                'admin_id': admin_id, 
                'person_id': person_id,
                'admin_type': admin_type,
                'role_name': role_name
            })
            
            # Store in fixed_accounts with the appropriate key
            account_name = config_key.replace('_config', '').replace('test_', '')
            self.data['fixed_accounts'][account_name] = {
                'person_id': person_id,
                'user_id': user_id,
                'admin_id': admin_id
            }
            
            self.add_statement(f"-- {role_name.upper()} ({account_name}): person={person_id}, user={user_id}, admin={admin_id}")
    
    # Insert all fixed accounts
    self.bulk_insert('person', 
                    ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 
                    'phone_number', 'citizen_id', 'address', 'profile_picture'], 
                    person_rows)
    
    self.bulk_insert('user_account', 
                    ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 
                    'role_id', 'role_name', 'account_status'], 
                    user_rows)
    
    if instructor_rows:
        self.bulk_insert('instructor', 
                        ['instructor_id', 'person_id', 'instructor_code', 'degree', 
                        'specialization', 'department_id', 'hire_date', 'employment_status'], 
                        instructor_rows)
    
    if admin_rows:
        self.bulk_insert('admin', 
                        ['admin_id', 'person_id', 'admin_code', 'position', 'admin_status'], 
                        admin_rows)

def create_regular_staff(self):
    self.add_statement("\n-- ==================== REGULAR INSTRUCTORS ====================")
    self.add_statement("-- NOTE: Only 5 fixed admin accounts exist (no regular admins)")
    
    first_names = self.names_config.get('first_names', '').split(', ')
    middle_names = self.names_config.get('middle_names', '').split(', ')
    last_names_male = self.names_config.get('last_names_male', '').split(', ')
    last_names_female = self.names_config.get('last_names_female', '').split(', ')
    
    person_rows = []
    user_rows = []
    instructor_rows = []
    instructor_role_id = self.role_id_map.get('Instructor')
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
        
        profile_pic = self.media_scanner.get_random_file('profile_pics')
        profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
        
        person_rows.append([person_id, full_name, dob, gender, email, phone, citizen_id, 
                        'TP Hồ Chí Minh', profile_pic_url])
        
        user_id = self.generate_uuid()
        username = f"gv{i+1:02d}"
        user_rows.append([user_id, person_id, username, 'hashed_pwd', 'salt', 
                        instructor_role_id, 'instructor', 'active'])
        
        instructor_id = self.generate_uuid()
        degree = random.choice(['Tiến sĩ', 'Thạc sĩ', 'Cử nhân'])
        specialization = random.choice(['Công nghệ thông tin', 'Kinh tế', 'Kỹ thuật', 'Khoa học'])
        hire_date = date(random.randint(2010, 2020), random.randint(1, 12), 1)
        instructor_rows.append([instructor_id, person_id, f"GV{i+1:04d}", degree, 
                            specialization, None, hire_date, 'active'])
        
        self.data['instructors'].append({
            'instructor_id': instructor_id, 
            'person_id': person_id, 
            'full_name': full_name
        })
    
    self.bulk_insert('person', 
                    ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 
                    'phone_number', 'citizen_id', 'address', 'profile_picture'], 
                    person_rows)
    
    self.bulk_insert('user_account', 
                    ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 
                    'role_id', 'role_name', 'account_status'], 
                    user_rows)
    
    self.bulk_insert('instructor', 
                    ['instructor_id', 'person_id', 'instructor_code', 'degree', 
                    'specialization', 'department_id', 'hire_date', 'employment_status'], 
                    instructor_rows)


def create_students(self):
    self.add_statement("\n-- ==================== STUDENTS ====================")
    self.add_statement("-- NOTE: Fixed STUDENT person/user already created")
    self.add_statement("-- Enrollment status distribution: 80% active, 10% graduated, 5% suspended, 3% dropped_out, 2% inactive")
    
    first_names = self.names_config.get('first_names', '').split(', ')
    middle_names = self.names_config.get('middle_names', '').split(', ')
    last_names_male = self.names_config.get('last_names_male', '').split(', ')
    last_names_female = self.names_config.get('last_names_female', '').split(', ')
    
    students_per_class = int(self.students_config.get('students_per_class', 30))
    global_counter = 1
    
    person_rows = []
    user_rows = []
    student_rows = []
    student_role_id = self.role_id_map.get('Student')
    
    if not student_role_id:
        self.add_statement("-- ERROR: Student role not found! Cannot create students.")
        return
    
    # Define enrollment status weights (must sum to 100)
    enrollment_statuses = [
        ('active', 80),
        ('graduated', 10),
        ('suspended', 5),
        ('dropped_out', 3),
        ('inactive', 2)
    ]
    
    def get_random_enrollment_status():
        """Weighted random selection of enrollment status"""
        rand = random.randint(1, 100)
        cumulative = 0
        for status, weight in enrollment_statuses:
            cumulative += weight
            if rand <= cumulative:
                return status
        return 'active'  # Fallback
    
    # Fixed student
    student_config = self.spec_data.get('test_student_config', {})
    target_class_year = int(student_config.get('class_year', 2023))
    target_class = next((c for c in self.data['classes'] if c['start_year'] == target_class_year), None)
    
    if target_class:
        student_id = student_config.get('student_id')
        person_id = self.data['fixed_accounts']['student']['person_id']
        student_code = student_config.get('student_code')
        
        self.data['fixed_accounts']['student']['class_id'] = target_class['class_id']
        self.data['fixed_accounts']['student']['class_start_year'] = target_class_year
        
        # Fixed student always has 'active' status
        student_rows.append([student_id, person_id, student_code, target_class['class_id'], 'active'])
        
        self.data['students'].append({
            'student_id': student_id,
            'person_id': person_id,
            'student_code': student_code,
            'class_id': target_class['class_id'],
            'class_start_year': target_class_year,
            'enrollment_status': 'active',
            'is_fixed': True
        })
        
        self.add_statement(f"-- Fixed STUDENT assigned to: {target_class['class_name']} (year {target_class_year})")
    else:
        self.add_statement(f"-- WARNING: Could not find class for year {target_class_year}, skipping fixed student")
    
    # Track status distribution for logging
    status_counts = {status: 0 for status, _ in enrollment_statuses}
    
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
            
            profile_pic = self.media_scanner.get_random_file('profile_pics')
            profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
            
            person_rows.append([person_id, full_name, dob, gender, email, phone, citizen_id, 
                            'TP Hồ Chí Minh', profile_pic_url])
            
            user_id = self.generate_uuid()
            username = f"sv{global_counter:05d}"
            user_rows.append([user_id, person_id, username, 'hashed_pwd', 'salt', 
                            student_role_id, 'student', 'active'])
            
            student_id = self.generate_uuid()
            student_code = f"SV{global_counter:06d}"
            
            # Get random enrollment status with weighted distribution
            enrollment_status = get_random_enrollment_status()
            status_counts[enrollment_status] += 1
            
            student_rows.append([student_id, person_id, student_code, cls['class_id'], enrollment_status])
            
            self.data['students'].append({
                'student_id': student_id,
                'person_id': person_id,
                'student_code': student_code,
                'class_id': cls['class_id'],
                'class_start_year': cls['start_year'],
                'enrollment_status': enrollment_status,
                'is_fixed': False
            })
            
            global_counter += 1
    
    # Log statistics
    self.add_statement(f"-- Total students: {len(student_rows)}")
    self.add_statement(f"-- Fixed: 1, Regular: {len(student_rows) - 1}")
    self.add_statement("-- Enrollment status distribution:")
    for status, count in status_counts.items():
        percentage = (count / (len(student_rows) - 1) * 100) if len(student_rows) > 1 else 0
        self.add_statement(f"--   {status}: {count} ({percentage:.1f}%)")
    
    if person_rows:
        self.bulk_insert('person', 
                        ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 
                        'phone_number', 'citizen_id', 'address', 'profile_picture'], 
                        person_rows)
    
    if user_rows:
        self.bulk_insert('user_account', 
                        ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 
                        'role_id', 'role_name', 'account_status'], 
                        user_rows)
    
    if student_rows:
        self.bulk_insert('student', 
                        ['student_id', 'person_id', 'student_code', 'class_id', 'enrollment_status'], 
                        student_rows)


from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_fixed_test_accounts = create_fixed_test_accounts
SQLDataGenerator.create_regular_staff = create_regular_staff
SQLDataGenerator.create_students = create_students