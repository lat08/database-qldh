import random
import base64
from datetime import date
from .config import *


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
    
    # Get role IDs
    student_role_id = self.role_id_map.get('Student')
    instructor_role_id = self.role_id_map.get('Instructor')
    
    # ============================================================
    # STUDENT ACCOUNT
    # ============================================================
    person_id = self.test_config.get('student_person_id')
    user_id = self.test_config.get('student_user_id')
    student_id = self.test_config.get('student_id')
    
    profile_pic = self.media_scanner.get_random_file('profile_pics')
    profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
    
    person_rows.append([
        person_id, 
        self.test_config.get('student_name'),
        self.test_config.get('student_dob'),
        self.test_config.get('student_gender'),
        self.test_config.get('student_email'),
        self.test_config.get('student_phone'),
        f"{random.randint(100000000000, 999999999999)}",
        'TP Hồ Chí Minh',
        profile_pic_url
    ])
    
    user_rows.append([
        user_id, 
        person_id, 
        self.test_config.get('student_username'),
        password_hash, 
        salt_b64, 
        student_role_id,
        'active'
    ])
    
    # Store for later use
    self.data['fixed_accounts']['student'] = {
        'person_id': person_id,
        'user_id': user_id,
        'student_id': student_id,
        'class_id': None  # Will be set during class creation
    }
    
    self.add_statement(f"-- STUDENT IDs: person={person_id}, user={user_id}, student={student_id}")
    
    # ============================================================
    # INSTRUCTOR ACCOUNT
    # ============================================================
    person_id = self.test_config.get('instructor_person_id')
    user_id = self.test_config.get('instructor_user_id')
    instructor_id = self.test_config.get('instructor_id')
    
    profile_pic = self.media_scanner.get_random_file('profile_pics')
    profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
    
    person_rows.append([
        person_id, 
        self.test_config.get('instructor_name'),
        self.test_config.get('instructor_dob'),
        self.test_config.get('instructor_gender'),
        self.test_config.get('instructor_email'),
        self.test_config.get('instructor_phone'),
        f"{random.randint(100000000000, 999999999999)}",
        'TP Hồ Chí Minh',
        profile_pic_url
    ])
    
    user_rows.append([
        user_id, 
        person_id, 
        self.test_config.get('instructor_username'),
        password_hash, 
        salt_b64, 
        instructor_role_id,
        'active'
    ])
    
    instructor_rows.append([
        instructor_id, 
        person_id, 
        self.test_config.get('instructor_code'),
        self.test_config.get('instructor_degree'), 
        self.test_config.get('instructor_specialization'),
        None,  # department_id
        self.test_config.get('instructor_hire_date'), 
        'active'
    ])
    
    self.data['instructors'].append({
        'instructor_id': instructor_id, 
        'person_id': person_id,
        'full_name': self.test_config.get('instructor_name')
    })
    
    self.data['fixed_accounts']['instructor'] = {
        'person_id': person_id,
        'user_id': user_id,
        'instructor_id': instructor_id,
        'full_name': self.test_config.get('instructor_name')
    }
    
    self.add_statement(f"-- INSTRUCTOR IDs: person={person_id}, user={user_id}, instructor={instructor_id}")
    
    # ============================================================
    # ADMIN ACCOUNTS (5 types)
    # ============================================================
    admin_types = [
        ('principal', 'Admin_Principal'),
        ('accountant', 'Admin_Accountant'),
        ('academic', 'Admin_Academic'),
        ('hr', 'Admin_HR'),
        ('facilities', 'Admin_Facilities')
    ]
    
    for admin_type, role_name in admin_types:
        person_id = self.test_config.get(f'{admin_type}_person_id')
        user_id = self.test_config.get(f'{admin_type}_user_id')
        admin_id = self.test_config.get(f'{admin_type}_admin_id')
        
        role_id = self.role_id_map.get(role_name)
        
        profile_pic = self.media_scanner.get_random_file('profile_pics')
        profile_pic_url = self.media_scanner.build_url('profile_pics', profile_pic) if profile_pic else None
        
        person_rows.append([
            person_id,
            self.test_config.get(f'{admin_type}_name'),
            self.test_config.get(f'{admin_type}_dob'),
            self.test_config.get(f'{admin_type}_gender'),
            self.test_config.get(f'{admin_type}_email'),
            self.test_config.get(f'{admin_type}_phone'),
            f"{random.randint(100000000000, 999999999999)}",
            'TP Hồ Chí Minh',
            profile_pic_url
        ])
        
        user_rows.append([
            user_id, 
            person_id, 
            self.test_config.get(f'{admin_type}_username'),
            password_hash, 
            salt_b64, 
            role_id,
            'active'
        ])
        
        admin_rows.append([
            admin_id, 
            person_id, 
            self.test_config.get(f'{admin_type}_code'), 
            self.test_config.get(f'{admin_type}_position'), 
            'active'
        ])
        
        self.data['admins'].append({
            'admin_id': admin_id, 
            'person_id': person_id,
            'admin_type': admin_type,
            'role_name': role_name
        })
        
        # Store principal as default admin for references
        if admin_type == 'principal':
            self.data['fixed_accounts']['admin'] = {
                'person_id': person_id,
                'user_id': user_id,
                'admin_id': admin_id
            }
        
        self.add_statement(f"-- {role_name.upper()} IDs: person={person_id}, user={user_id}, admin={admin_id}")
    
    # Insert all fixed accounts
    self.bulk_insert('person', 
                    ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 
                    'phone_number', 'citizen_id', 'address', 'profile_picture'], 
                    person_rows)
    
    self.bulk_insert('user_account', 
                    ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 
                    'role_id', 'account_status'], 
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
    
    # Instructors only
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
                        instructor_role_id, 'active'])
        
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
                    'role_id', 'account_status'], 
                    user_rows)
    
    self.bulk_insert('instructor', 
                    ['instructor_id', 'person_id', 'instructor_code', 'degree', 
                    'specialization', 'department_id', 'hire_date', 'employment_status'], 
                    instructor_rows)

def create_students(self):
    self.add_statement("\n-- ==================== STUDENTS ====================")
    self.add_statement("-- NOTE: Fixed STUDENT account already created in create_fixed_test_accounts()")
    self.add_statement("-- Only creating regular students here")
    
    first_names = self.names_config.get('first_names', '').split(', ')
    middle_names = self.names_config.get('middle_names', '').split(', ')
    last_names_male = self.names_config.get('last_names_male', '').split(', ')
    last_names_female = self.names_config.get('last_names_female', '').split(', ')
    
    students_per_class = int(self.students_config.get('students_per_class', 30))
    global_counter = 1
    
    person_rows = []
    user_rows = []
    student_rows = []
    
    # Get Student role ID
    student_role_id = self.role_id_map.get('Student')
    
    if not student_role_id:
        self.add_statement("-- ERROR: Student role not found! Cannot create students.")
        return
    
    # Find target class for fixed student and update metadata only
    target_class_year = int(self.test_config.get('student_class_year', 2023))
    target_class = next((c for c in self.data['classes'] if c['start_year'] == target_class_year), None)
    
    if target_class:
        student_id = self.test_config.get('student_id', '00000000-0000-0000-0000-000000000003')
        person_id = self.data['fixed_accounts']['student']['person_id']
        
        # Update fixed account with class info (person/user already created)
        self.data['fixed_accounts']['student']['class_id'] = target_class['class_id']
        self.data['fixed_accounts']['student']['class_start_year'] = target_class_year
        
        # ONLY insert student record (person/user already exist from create_fixed_test_accounts)
        student_rows.append([
            student_id, 
            person_id, 
            self.test_config.get('student_code'),
            target_class['class_id'], 
            'active'
        ])
        
        # Add to students list
        self.data['students'].append({
            'student_id': student_id,
            'person_id': person_id,
            'student_code': self.test_config.get('student_code'),
            'class_id': target_class['class_id'],
            'class_start_year': target_class_year,
            'is_fixed': True
        })
        
        self.add_statement(f"-- Fixed STUDENT assigned to class: {target_class['class_name']} (year {target_class_year})")
    else:
        self.add_statement(f"-- WARNING: Could not find class for year {target_class_year}, skipping fixed student")
    
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
            
            person_rows.append([
                person_id, 
                full_name, 
                dob, 
                gender, 
                email, 
                phone, 
                citizen_id, 
                'TP Hồ Chí Minh', 
                profile_pic_url
            ])
            
            user_id = self.generate_uuid()
            username = f"sv{global_counter:05d}"
            user_rows.append([
                user_id, 
                person_id, 
                username, 
                'hashed_pwd', 
                'salt', 
                student_role_id, 
                'active'
            ])
            
            student_id = self.generate_uuid()
            student_code = f"SV{global_counter:06d}"
            student_rows.append([
                student_id, 
                person_id, 
                student_code, 
                cls['class_id'], 
                'active'
            ])
            
            self.data['students'].append({
                'student_id': student_id,
                'person_id': person_id,
                'student_code': student_code,
                'class_id': cls['class_id'],
                'class_start_year': cls['start_year'],
                'is_fixed': False
            })
            
            global_counter += 1
    
    self.add_statement(f"-- Total students to create: {len(student_rows)}")
    self.add_statement(f"-- Fixed student: 1 (student record only)")
    self.add_statement(f"-- Regular students: {len(student_rows) - 1}")
    
    # Insert person/user ONLY for regular students (fixed student already has these)
    if person_rows:
        self.bulk_insert('person', 
                        ['person_id', 'full_name', 'date_of_birth', 'gender', 'email', 
                        'phone_number', 'citizen_id', 'address', 'profile_picture'], 
                        person_rows)
    
    if user_rows:
        self.bulk_insert('user_account', 
                        ['user_id', 'person_id', 'username', 'password_hash', 'password_salt', 
                        'role_id', 'account_status'], 
                        user_rows)
    
    # Insert ALL student records (fixed + regular)
    if student_rows:
        self.bulk_insert('student', 
                        ['student_id', 'person_id', 'student_code', 'class_id', 'enrollment_status'], 
                        student_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_fixed_test_accounts = create_fixed_test_accounts
SQLDataGenerator.create_regular_staff = create_regular_staff
SQLDataGenerator.create_students = create_students