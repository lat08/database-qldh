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
        dean_id = random.choice(self.data['instructors'])['instructor_id'] if self.data['instructors'] else None
        
        self.data['faculties'].append({
            'faculty_id': faculty_id, 
            'faculty_name': fac_name, 
            'faculty_code': fac_code
        })
        
        faculty_rows.append([faculty_id, fac_name, fac_code, dean_id, 'active'])
        
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
    
    self.bulk_insert('faculty', 
                    ['faculty_id', 'faculty_name', 'faculty_code', 'dean_id', 'faculty_status'], 
                    faculty_rows)
    
    self.bulk_insert('department', 
                    ['department_id', 'department_name', 'department_code', 'faculty_id'], 
                    department_rows)

def update_instructor_faculty_assignments(self):
    self.add_statement("\n-- ==================== ASSIGNING INSTRUCTORS TO FACULTIES ====================")
    
    if not self.data['faculties'] or not self.data['instructors']:
        raise RuntimeError("Cannot assign instructors to faculties: missing faculties or instructors")
    
    update_statements = []
    
    for instructor in self.data['instructors']:
        faculty = random.choice(self.data['faculties'])
        update_statements.append(
            f"UPDATE instructor SET faculty_id = '{faculty['faculty_id']}' "
            f"WHERE instructor_id = '{instructor['instructor_id']}';"
        )
    
    for stmt in update_statements:
        self.add_statement(stmt)
    
    self.add_statement(f"-- Assigned {len(update_statements)} instructors to faculties")

def create_academic_years_and_semesters(self):
    """
    UPDATED: Proper semester transitions with consistent registration windows
    - Registration starts 10-15 days before semester (adjusted to Monday)
    - Registration ends 1 day before semester starts
    - TODAY (datetime.now()) guaranteed within Fall 2025 registration period
    - START DATES: Always Monday | END DATES: Always Sunday
    - Summer 2024-2025 ends on 11/20/2025
    - Fall 2025 starts on 11/24/2025, registration starts on 11/8/2025
    """
    from datetime import timedelta, date, datetime
    
    def to_next_monday(d):
        """Move to next Monday if not already Monday"""
        days_ahead = (7 - d.weekday()) % 7
        if days_ahead == 0:
            return d
        return d + timedelta(days=days_ahead)
    
    def to_next_sunday(d):
        """Move to next Sunday if not already Sunday"""
        days_ahead = (6 - d.weekday()) % 7
        if days_ahead == 0:
            return d
        return d + timedelta(days=days_ahead)
    
    def to_prev_monday(d):
        """Move to previous Monday if not already Monday"""
        if d.weekday() == 0:
            return d
        return d - timedelta(days=d.weekday())
    
    self.add_statement("\n-- ==================== ACADEMIC YEARS & SEMESTERS ====================")
    self.add_statement("-- Registration starts 10-15 days before semester (Monday)")
    self.add_statement("-- Registration ends 1 day before semester starts")
    self.add_statement("-- TODAY (datetime.now()) guaranteed within Fall 2025 registration")
    self.add_statement("-- START DATES: Always Monday | END DATES: Always Sunday")
    self.add_statement("-- Summer 2024-2025 ends on 11/20/2025")
    self.add_statement("-- Fall 2025 starts on 11/24/2025, registration starts on 11/8/2025")
    
    ay_rows = []
    sem_rows = []
    
    academic_years_config = self.spec_data.get('academic_years_config', {})
    TODAY = datetime.now().date()  # Dynamic current date
    
    for year_range, details in academic_years_config.items():
        date_range = details.split('to')
        raw_start = datetime.strptime(date_range[0].strip(), '%Y-%m-%d').date()
        raw_end = datetime.strptime(date_range[1].split(',')[0].strip(), '%Y-%m-%d').date()
        status = details.split(',')[1].strip()
        
        start_date = to_next_monday(raw_start)
        end_date = to_next_sunday(raw_end)
        
        academic_year_id = self.generate_uuid()
        start_year = int(year_range.split('-')[0])
        end_year = int(year_range.split('-')[1])
        
        self.data['academic_years'].append({
            'academic_year_id': academic_year_id,
            'start_year': start_year,
            'end_year': end_year
        })
        
        ay_rows.append([academic_year_id, year_range, start_date, end_date, status])
        
        # Define semester base dates
        if start_year == 2025:
            # Fall 2025: start on 11/24, registration starts on 11/8
            semesters_info = [
                ('fall', f'Học kỳ 1 ({start_year}-{end_year})', date(2025, 11, 24), date(2025, 12, 31)),
                ('spring', f'Học kỳ 2 ({start_year}-{end_year})', date(end_year, 1, 11), date(end_year, 5, 31)),
                ('summer', f'Học kỳ hè ({start_year}-{end_year})', date(end_year, 6, 11), date(end_year, 10, 31))
            ]
        elif start_year == 2024:
            # Summer 2024-2025: ends on 11/20/2025
            semesters_info = [
                ('fall', f'Học kỳ 1 ({start_year}-{end_year})', date(start_year, 9, 11), date(start_year, 12, 31)),
                ('spring', f'Học kỳ 2 ({start_year}-{end_year})', date(end_year, 1, 11), date(end_year, 5, 31)),
                ('summer', f'Học kỳ hè ({start_year}-{end_year})', date(end_year, 6, 11), date(2025, 11, 20))
            ]
        else:
            semesters_info = [
                ('fall', f'Học kỳ 1 ({start_year}-{end_year})', date(start_year, 9, 11), date(start_year, 12, 31)),
                ('spring', f'Học kỳ 2 ({start_year}-{end_year})', date(end_year, 1, 11), date(end_year, 5, 31)),
                ('summer', f'Học kỳ hè ({start_year}-{end_year})', date(end_year, 6, 11), date(end_year, 8, 31))
            ]
        
        for sem_type, sem_name, raw_sem_start, raw_sem_end in semesters_info:
            # Adjust semester dates to Monday/Sunday
            sem_start = to_next_monday(raw_sem_start)
            sem_end = to_next_sunday(raw_sem_end)
            
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
            
            # SPECIAL HANDLING FOR FALL 2025: Set fixed dates as required
            if start_year == 2025 and sem_type == 'fall':
                # Fixed dates: start on 11/24, registration starts on 11/8
                sem_start = date(2025, 11, 24)
                sem_start = to_next_monday(sem_start)  # Ensure it's Monday
                reg_start = date(2025, 11, 8)
                reg_end = sem_start - timedelta(days=1)  # 1 day before semester starts
                
                # Update the semester start date in data
                self.data['semesters'][-1]['start_date'] = sem_start
                
                # Ensure TODAY is within registration period (if not, adjust registration window)
                if TODAY < reg_start:
                    # If TODAY is before registration start, extend registration backward
                    reg_start = to_prev_monday(TODAY - timedelta(days=2))
                elif TODAY > reg_end:
                    # If TODAY is after registration end, extend registration forward
                    reg_end = TODAY + timedelta(days=2)
                    sem_start = to_next_monday(reg_end + timedelta(days=1))
                    self.data['semesters'][-1]['start_date'] = sem_start
                
                self.add_statement(f"-- {sem_name}: Fixed dates - Start: {sem_start}, Registration: {reg_start} to {reg_end}")
                self.add_statement(f"-- TODAY ({TODAY}) is within registration: {reg_start <= TODAY <= reg_end}")
                
            else:
                # NORMAL SEMESTERS: Standard registration calculation
                # Registration ends 1 day before semester starts
                reg_end = sem_start - timedelta(days=1)
                
                # Registration starts 12 days before semester, adjusted to Monday
                reg_start_raw = sem_start - timedelta(days=12)
                reg_start = to_prev_monday(reg_start_raw)
                
                # Ensure we have at least 7 days registration period
                if (reg_end - reg_start).days < 7:
                    reg_start = reg_end - timedelta(days=7)
                    reg_start = to_prev_monday(reg_start)
            
            # Log the registration window
            days_before = (sem_start - reg_start).days
            self.add_statement(f"-- {sem_name}: Registration {days_before} days before semester")
            
            sem_rows.append([
                semester_id, 
                sem_name, 
                academic_year_id, 
                sem_type, 
                sem_start, 
                sem_end, 
                reg_start, 
                reg_end, 
                'active'
            ])
    
    self.bulk_insert('academic_year', 
                    ['academic_year_id', 'year_name', 'start_date', 'end_date', 'academic_year_status'], 
                    ay_rows)
    self.bulk_insert('semester', 
                    ['semester_id', 'semester_name', 'academic_year_id', 'semester_type', 
                     'start_date', 'end_date', 'registration_start_date', 'registration_end_date', 
                     'semester_status'], 
                    sem_rows)

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

def create_curricula(self):
    self.add_statement("\n-- ==================== CURRICULA ====================")
    
    curriculum_rows = []
    admin_id = self.data['fixed_accounts'].get('admin', {}).get('admin_id')
    
    for dept in self.data['departments']:
        for year in range(2021, 2026):
            curriculum_id = self.generate_uuid()
            curriculum_code = f"{dept['department_code']}-{year}"
            curriculum_name = f"Chương trình đào tạo {dept['department_name']} - Khóa {year}"
            
            self.data['curricula'].append({
                'curriculum_id': curriculum_id,
                'curriculum_code': curriculum_code,
                'curriculum_name': curriculum_name,
                'department_id': dept['department_id'],
                'applied_year': year,
                'version_number': 1
            })
            
            curriculum_rows.append([
                curriculum_id,
                curriculum_code,
                curriculum_name,
                dept['department_id'],
                year,
                1,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                None,
                admin_id,
                None,
                0,
                1
            ])
    
    self.add_statement(f"-- Generated {len(curriculum_rows)} curricula")
    
    self.bulk_insert('curriculum',
                    ['curriculum_id', 'curriculum_code', 'curriculum_name', 'department_id',
                     'applied_year', 'version_number', 'created_at', 'updated_at',
                     'created_by', 'updated_by', 'is_deleted', 'is_active'],
                    curriculum_rows)

def create_curriculum_details(self):
    """
    FIXED: Properly validates subject data before attempting to map
    """
    self.add_statement("\n-- ==================== CURRICULUM DETAILS ====================")
    
    curriculum_detail_rows = []
    admin_id = self.data['fixed_accounts'].get('admin', {}).get('admin_id')
    
    # Validate subjects exist
    if not self.data.get('subjects'):
        raise RuntimeError(
            "CRITICAL ERROR: No subjects found when creating curriculum_details!\n"
            "create_subjects() must be called BEFORE create_curriculum_details()"
        )
    
    # Validate subject data structure
    for subject in self.data['subjects']:
        if 'is_general' not in subject:
            raise RuntimeError(
                f"CRITICAL ERROR: Subject {subject.get('subject_code', '?')} missing 'is_general' flag!\n"
                "Subjects must have is_general=True/False for curriculum mapping to work"
            )
    
    for curriculum in self.data['curricula']:
        dept_id = curriculum['department_id']
        
        # Get subjects for this department
        dept_subjects = []
        
        # Add ALL general subjects (every curriculum needs these)
        general_subjects = [s for s in self.data['subjects'] if s['is_general'] == True]
        dept_subjects.extend(general_subjects)
        
        # Add specialized subjects for THIS department only
        specialized_subjects = [s for s in self.data['subjects'] 
                              if s['is_general'] == False 
                              and s.get('department_id') == dept_id]
        dept_subjects.extend(specialized_subjects)
        
        if not dept_subjects:
            raise RuntimeError(
                f"CRITICAL ERROR: No subjects found for curriculum {curriculum['curriculum_code']}!\n"
                f"  Department ID: {dept_id}\n"
                f"  Total subjects in system: {len(self.data['subjects'])}\n"
                f"  General subjects: {len(general_subjects)}\n"
                f"  Specialized subjects for this dept: {len(specialized_subjects)}"
            )
        
        # Distribute subjects across 4 years, 2 semesters per year
        total_subjects = len(dept_subjects)
        year1_count = int(total_subjects * 0.30)
        year2_count = int(total_subjects * 0.25)
        year3_count = int(total_subjects * 0.25)
        year4_count = total_subjects - year1_count - year2_count - year3_count
        
        subject_index = 0
        
        year_distributions = [
            (1, year1_count),
            (2, year2_count),
            (3, year3_count),
            (4, year4_count)
        ]
        
        for academic_year_index, count in year_distributions:
            semester1_count = int(count * 0.5)
            semester2_count = count - semester1_count
            
            semester_distributions = [
                (1, semester1_count),
                (2, semester2_count)
            ]
            
            for semester_index, sem_count in semester_distributions:
                for _ in range(sem_count):
                    if subject_index >= total_subjects:
                        break
                    
                    subject = dept_subjects[subject_index]
                    subject_index += 1
                    
                    curriculum_detail_id = self.generate_uuid()
                    
                    self.data['curriculum_details'].append({
                        'curriculum_detail_id': curriculum_detail_id,
                        'curriculum_id': curriculum['curriculum_id'],
                        'subject_id': subject['subject_id'],
                        'academic_year_index': academic_year_index,
                        'semester_index': semester_index
                    })
                    
                    curriculum_detail_rows.append([
                        curriculum_detail_id,
                        curriculum['curriculum_id'],
                        subject['subject_id'],
                        academic_year_index,
                        semester_index,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        None,
                        admin_id,
                        None,
                        0,
                        1
                    ])
    
    if len(curriculum_detail_rows) == 0:
        raise RuntimeError(
            "CRITICAL ERROR: No curriculum_details created!\n"
            "This will cause enrollment creation to fail"
        )
    
    self.add_statement(f"-- Generated {len(curriculum_detail_rows)} curriculum details")
    
    self.bulk_insert('curriculum_detail',
                    ['curriculum_detail_id', 'curriculum_id', 'subject_id',
                     'academic_year_index', 'semester_index',
                     'created_at', 'updated_at', 'created_by', 'updated_by',
                     'is_deleted', 'is_active'],
                    curriculum_detail_rows)

def create_classes(self):
    self.add_statement("\n-- ==================== CLASSES ====================")
    
    class_rows = []
    class_names = set()
    
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
        
        year = int(class_name[1:5])
        
        matching_ay = next((ay for ay in self.data['academic_years'] if ay['start_year'] == year), None)
        matching_dept = next((d for d in self.data['departments'] if d['department_name'] == dept_name), None)
        training_system_id = training_system_lookup.get(training_system_name)
        
        if not matching_ay or not matching_dept or not training_system_id:
            continue
        
        matching_curriculum = next(
            (c for c in self.data['curricula'] 
             if c['department_id'] == matching_dept['department_id'] 
             and c['applied_year'] == year),
            None
        )
        
        if not matching_curriculum:
            continue
        
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
            'curriculum_id': matching_curriculum['curriculum_id'],
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
            matching_curriculum['curriculum_id'],
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
        'curriculum_id',
        'advisor_instructor_id', 
        'training_system_id', 
        'start_academic_year_id',
        'end_academic_year_id',
        'class_status'
    ], class_rows)

# Register functions
from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_faculties_and_departments = create_faculties_and_departments
SQLDataGenerator.update_instructor_faculty_assignments = update_instructor_faculty_assignments
SQLDataGenerator.create_training_systems = create_training_systems
SQLDataGenerator.create_academic_years_and_semesters = create_academic_years_and_semesters
SQLDataGenerator.create_classes = create_classes
SQLDataGenerator.create_curricula = create_curricula
SQLDataGenerator.create_curriculum_details = create_curriculum_details