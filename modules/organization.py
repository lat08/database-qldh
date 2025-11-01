import random
from datetime import datetime, date, timedelta
from .config import *

def create_faculties_and_departments(self):
    self.add_statement("\n-- ==================== FACULTIES & DEPARTMENTS ====================")
    
    faculty_rows = []
    department_rows = []
    
    for line in self.spec_data.get('faculties', []):
        parts = [p.strip() for p in line.split('|')]
        fac_name, fac_code, dept_names = parts[0], parts[1], [d.strip() for d in parts[2].split(',')]
        
        faculty_id = self.generate_uuid()
        # Dean will be assigned randomly from instructors
        dean_id = random.choice(self.data['instructors'])['instructor_id'] if self.data['instructors'] else None
        
        self.data['faculties'].append({
            'faculty_id': faculty_id, 
            'faculty_name': fac_name, 
            'faculty_code': fac_code
        })
        
        faculty_rows.append([faculty_id, fac_name, fac_code, dean_id, 'active'])
        
        # Create departments under this faculty (no head_id needed)
        for idx, dept_name in enumerate(dept_names):
            dept_id = self.generate_uuid()
            dept_code = f"{fac_code}D{idx+1}"
            
            self.data['departments'].append({
                'department_id': dept_id,
                'department_name': dept_name,
                'department_code': dept_code,
                'faculty_id': faculty_id
            })
            
            department_rows.append([dept_id, dept_name, dept_code, faculty_id])
    
    # Insert faculties
    self.bulk_insert('faculty', 
                    ['faculty_id', 'faculty_name', 'faculty_code', 'dean_id', 'faculty_status'], 
                    faculty_rows)
    
    # Insert departments (no head_of_department_id)
    self.bulk_insert('department', 
                    ['department_id', 'department_name', 'department_code', 'faculty_id'], 
                    department_rows)


def update_instructor_faculty_assignments(self):
    """Assign instructors to faculties after faculties are created"""
    self.add_statement("\n-- ==================== ASSIGNING INSTRUCTORS TO FACULTIES ====================")
    
    if not self.data['faculties'] or not self.data['instructors']:
        self.add_statement("-- WARNING: No faculties or instructors available for assignment")
        return
    
    update_statements = []
    
    # Assign each instructor to a random faculty
    for instructor in self.data['instructors']:
        faculty = random.choice(self.data['faculties'])
        update_statements.append(
            f"UPDATE instructor SET faculty_id = '{faculty['faculty_id']}' "
            f"WHERE instructor_id = '{instructor['instructor_id']}';"
        )
    
    # Execute updates
    for stmt in update_statements:
        self.add_statement(stmt)
    
    self.add_statement(f"-- Assigned {len(update_statements)} instructors to faculties")

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

def create_training_systems(self):
    self.add_statement("\n-- ==================== TRAINING SYSTEMS ====================")
    
    training_system_rows = []
    
    for line in self.spec_data.get('training_systems', []):
        parts = [p.strip() for p in line.split('|')]
        system_name = parts[0]
        description = parts[1] if len(parts) > 1 else ''
        
        training_system_id = self.generate_uuid()
        
        self.data['training_systems'].append({
            'training_system_id': training_system_id,
            'training_system_name': system_name
        })
        
        training_system_rows.append([training_system_id, system_name, description])
    
    self.bulk_insert('training_system', 
                    ['training_system_id', 'training_system_name', 'description'], 
                    training_system_rows)

def create_classes(self):
    self.add_statement("\n-- ==================== CLASSES ====================")
    
    class_rows = []
    class_names = set()
    
    # Build training system lookup
    training_system_lookup = {ts['training_system_name']: ts['training_system_id'] 
                             for ts in self.data['training_systems']}
    
    for line in self.spec_data.get('class_curricula', []):
        parts = [p.strip() for p in line.split('|')]
        class_name = parts[0]
        dept_name = parts[1]
        training_system_name = parts[2]
        
        if class_name in class_names:
            continue
        class_names.add(class_name)
        
        # Extract year from class name (e.g., K2023-1 -> 2023)
        year = int(class_name[1:5])
        
        # Find matching academic year, department, and training system
        matching_ay = next((ay for ay in self.data['academic_years'] if ay['start_year'] == year), None)
        matching_dept = next((d for d in self.data['departments'] if d['department_name'] == dept_name), None)
        training_system_id = training_system_lookup.get(training_system_name)
        
        if not matching_ay or not matching_dept or not training_system_id:
            self.add_statement(f"-- WARNING: Missing data for {class_name}")
            continue
        
        # Calculate end_academic_year_id (4-year program)
        end_year = year + 4
        end_academic_year = next((ay for ay in self.data['academic_years'] 
                                 if ay['start_year'] == end_year), None)
        
        if not end_academic_year:
            end_academic_year = max(self.data['academic_years'], 
                                   key=lambda x: x['start_year'])
        
        end_academic_year_id = end_academic_year['academic_year_id']
        
        class_id = self.generate_uuid()
        class_code = class_name
        advisor_id = random.choice(self.data['instructors'])['instructor_id']
        
        self.data['classes'].append({
            'class_id': class_id,
            'class_code': class_code,
            'class_name': class_name,
            'department_id': matching_dept['department_id'],
            'training_system_id': training_system_id,
            'start_academic_year_id': matching_ay['academic_year_id'],
            'end_academic_year_id': end_academic_year_id,
            'start_year': year,
            'department_name': dept_name,
            'training_system_name': training_system_name
        })
        
        class_rows.append([
            class_id, 
            class_code, 
            class_name, 
            matching_dept['department_id'], 
            advisor_id, 
            training_system_id, 
            matching_ay['academic_year_id'],
            end_academic_year_id,
            'active'
        ])
    
    self.bulk_insert('class', [
        'class_id', 
        'class_code', 
        'class_name', 
        'department_id', 
        'advisor_instructor_id', 
        'training_system_id', 
        'start_academic_year_id',
        'end_academic_year_id',
        'class_status'
    ], class_rows)

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
        if len(parts) < 4:  # Changed from 3 to 4
            self.add_statement(f"-- WARNING: Invalid curriculum line for {cls['class_code']}")
            cls['curriculum'] = []
            continue
        
        subject_codes_str = parts[3]  # Changed from parts[2] to parts[3]
        
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

# Register the updated functions
from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_faculties_and_departments = create_faculties_and_departments
SQLDataGenerator.update_instructor_faculty_assignments = update_instructor_faculty_assignments
SQLDataGenerator.create_training_systems = create_training_systems
SQLDataGenerator.create_academic_years_and_semesters = create_academic_years_and_semesters
SQLDataGenerator.create_classes = create_classes
SQLDataGenerator.map_class_curricula = map_class_curricula