import random
from collections import defaultdict
from datetime import datetime, timedelta, date
from .config import *

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
            
            course_rows.append([course_id, subject['subject_id'], semester['semester_id'], fee, 'active'])
    
    self.add_statement(f"-- Total courses generated: {len(course_rows)}")
    self.bulk_insert('course', ['course_id', 'subject_id', 'semester_id', 'fee_per_credit', 'course_status'], course_rows)


def create_course_classes(self):
    """
    FIXED: Create course classes with proper conflict detection
    - Prevents room scheduling conflicts
    - Prevents instructor scheduling conflicts
    """
    self.add_statement("\n-- ==================== COURSE CLASSES (DEMAND-BASED) ====================")
    self.add_statement("-- Classes created based on student curriculum requirements")
    self.add_statement("-- Section size: 25-45 students")
    self.add_statement("-- Proper schedule conflict detection (room AND instructor)")
    
    course_class_rows = []
    
    # Get admin user for grade approval
    admin_id = self.data['fixed_accounts']['admin']['admin_id']
    
    # Calculate students who NEED each course (based on curriculum)
    course_demand = defaultdict(set)
    
    for student in self.data['students']:
        class_id = student['class_id']
        cls = next((c for c in self.data['classes'] if c['class_id'] == class_id), None)
        if not cls:
            continue
        
        curriculum_id = cls.get('curriculum_id')
        if not curriculum_id:
            continue
        
        curriculum_subject_ids = set()
        for cd in self.data.get('curriculum_details', []):
            if cd['curriculum_id'] == curriculum_id:
                curriculum_subject_ids.add(cd['subject_id'])
        
        if not curriculum_subject_ids:
            continue
        
        for course in self.data['courses']:
            if course['subject_id'] in curriculum_subject_ids:
                if course['start_year'] >= student['class_start_year']:
                    if course['start_year'] > 2025:
                        continue
                    if course['start_year'] == 2025 and course['semester_type'] == 'summer':
                        continue
                    # Allow summer 2024-2025 courses (start_year == 2024, semester_type == 'summer')
                    
                    course_demand[course['course_id']].add(student['student_id'])
    
    # SPECIAL: Ensure test student creates demand for summer 2024-2025 courses
    # This ensures course classes are created for summer 2024-2025 even if no other students need them
    test_student_id = self.data['fixed_accounts'].get('student', {}).get('student_id')
    if test_student_id:
        test_student = next((s for s in self.data['students'] if s['student_id'] == test_student_id), None)
        if test_student:
            test_student_class_id = test_student['class_id']
            test_student_class = next((c for c in self.data['classes'] if c['class_id'] == test_student_class_id), None)
            if test_student_class:
                curriculum_id = test_student_class.get('curriculum_id')
                curriculum_subject_ids = set()
                for cd in self.data.get('curriculum_details', []):
                    if cd['curriculum_id'] == curriculum_id:
                        curriculum_subject_ids.add(cd['subject_id'])
                
                # Find summer 2024-2025 semester
                summer_2024_2025_semester = None
                for sem in self.data['semesters']:
                    if sem['start_year'] == 2024 and sem['semester_type'] == 'summer':
                        summer_2024_2025_semester = sem
                        break
                
                if summer_2024_2025_semester:
                    # Add demand for all summer 2024-2025 courses (curriculum and non-curriculum)
                    for course in self.data['courses']:
                        if course['semester_id'] == summer_2024_2025_semester['semester_id']:
                            course_demand[course['course_id']].add(test_student_id)
    
    # Day combinations for scheduling
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
    
    # Time slots
    time_slots = [
        (1, 5),
        (6, 9),
        (10, 12)
    ]
    
    # FIXED: Track room usage with proper conflict detection
    # Key: (room_id, semester_id, day, period) -> course_class_id
    room_usage = {}
    
    # FIXED: Track instructor usage to prevent scheduling conflicts
    # Key: (instructor_id, semester_id, day, period) -> course_class_id
    instructor_usage = {}
    
    grade_workflow_stats = {
        'approved': 0,
        'pending': 0,
        'draft': 0
    }
    
    courses_with_no_demand = 0
    sections_created = 0
    sections_skipped = 0
    
    # UPDATED: Create course classes for:
    # - Past semesters (start_year < 2025) - already completed
    # - Summer 2024-2025 (start_year == 2024 and semester_type == 'summer') - current/ongoing semester
    # - Fall 2025 (start_year == 2025 and semester_type == 'fall') - CURRENT registration period
    # We should NOT open course classes for:
    # - Spring/Summer 2025 (start_year == 2025 and semester_type != 'fall') - future semesters
    # - Any year > 2025 - future academic years
    
    for course in self.data['courses']:
        # Filter: Skip future years (2026+)
        if course['start_year'] > 2025:
            continue
        # Filter: Skip Spring/Summer 2025 (only allow Fall 2025 for year 2025)
        if course['start_year'] == 2025 and course['semester_type'] != 'fall':
            continue
        # At this point, we keep:
        # - All past semesters (start_year < 2024)
        # - Summer 2024-2025 (start_year == 2024 and semester_type == 'summer') - for test student
        # - Fall 2024 (start_year == 2024 and semester_type == 'fall')
        # - Spring 2024-2025 (start_year == 2024 and semester_type == 'spring')
        # - Fall 2025 (start_year == 2025 and semester_type == 'fall')

        total_hours = course['theory_hours'] + course['practice_hours']
        if total_hours == 0:
            continue
        
        potential_students = course_demand.get(course['course_id'], set())
        num_students = len(potential_students)
        
        # For summer 2024-2025, ensure at least one course class is created even with minimal demand
        # This is important for test student enrollment
        is_summer_2024_2025 = (course['start_year'] == 2024 and course['semester_type'] == 'summer')
        
        if num_students == 0 and not is_summer_2024_2025:
            courses_with_no_demand += 1
            continue
        
        # For summer 2024-2025 with test student, ensure at least 1 section
        if is_summer_2024_2025 and num_students == 0:
            num_students = 1  # Create at least 1 section for test student
        
        # FIXED: Better section calculation (25-45 students per section)
        min_per_section = 25
        max_per_section = 45
        num_sections = max(1, (num_students + max_per_section - 1) // max_per_section)
        
        for session_idx in range(num_sections):
            # Try to find conflict-free slot
            scheduled = False
            attempts = 0
            max_attempts = 200
            
            while not scheduled and attempts < max_attempts:
                attempts += 1
                
                # FIXED: Select instructor INSIDE the loop to try different instructors
                if course['start_year'] == 2025 and course['semester_type'] == 'fall' and random.random() < 0.3:
                    instructor_id = self.data['fixed_accounts']['instructor']['instructor_id']
                else:
                    instructor_id = random.choice(self.data['instructors'])['instructor_id']
                
                room = random.choice(self.data['rooms'])
                days = random.choice(day_combinations)
                time_slot = random.choice(time_slots)
                
                # FIXED: Check BOTH room AND instructor conflicts
                conflict = False
                for day in days:
                    for period in range(time_slot[0], time_slot[1] + 1):
                        # Check room conflict
                        room_key = (room['room_id'], course['semester_id'], day, period)
                        if room_key in room_usage:
                            conflict = True
                            break
                        
                        # Check instructor conflict
                        instructor_key = (instructor_id, course['semester_id'], day, period)
                        if instructor_key in instructor_usage:
                            conflict = True
                            break
                    
                    if conflict:
                        break
                
                if not conflict:
                    course_class_id = self.generate_uuid()
                    
                    # FIXED: Mark ALL time slots as used for BOTH room AND instructor
                    for day in days:
                        for period in range(time_slot[0], time_slot[1] + 1):
                            room_key = (room['room_id'], course['semester_id'], day, period)
                            room_usage[room_key] = course_class_id
                            
                            instructor_key = (instructor_id, course['semester_id'], day, period)
                            instructor_usage[instructor_key] = course_class_id
                    
                    # Calculate dates
                    course_start_date = course['semester_start']
                    course_end_date = course['semester_end']
                    
                    if isinstance(course_start_date, str):
                        course_start_date = datetime.strptime(course_start_date, '%Y-%m-%d').date()
                    if isinstance(course_end_date, str):
                        course_end_date = datetime.strptime(course_end_date, '%Y-%m-%d').date()
                    
                    first_day = days[0]
                    semester_weekday = course_start_date.weekday()
                    target_weekday = first_day - 2
                    days_until_first = (target_weekday - semester_weekday) % 7
                    actual_start_date = course_start_date + timedelta(days=days_until_first)
                    
                    # FIXED: Better capacity calculation
                    if session_idx == num_sections - 1:
                        remaining = num_students - (session_idx * max_per_section)
                        session_max_students = min(remaining + 5, max_per_section)
                    else:
                        session_max_students = random.randint(min_per_section, max_per_section)
                    
                    # Determine grade submission status
                    # Summer 2024-2025 is current/ongoing, so it should have draft or pending status
                    is_summer_2024_2025 = (course['start_year'] == 2024 and course['semester_type'] == 'summer')
                    is_past = (course['start_year'] < 2024) or \
                             (course['start_year'] == 2024 and course['semester_type'] in ('fall', 'spring')) or \
                             (course['start_year'] == 2025 and course['semester_type'] == 'spring')
                    is_current = (course['start_year'] == 2025 and course['semester_type'] == 'fall') or is_summer_2024_2025
                    
                    grade_submission_status = 'draft'
                    grade_submitted_at = None
                    grade_approved_at = None
                    grade_approved_by = None
                    grade_submission_note = None
                    grade_approval_note = None
                    
                    if is_past:
                        grade_submission_status = 'approved'
                        semester_end_date = course_end_date
                        submit_date = datetime.combine(semester_end_date, datetime.min.time()) - timedelta(days=random.randint(3, 7))
                        grade_submitted_at = submit_date.strftime('%Y-%m-%d %H:%M:%S')
                        approve_date = submit_date + timedelta(days=random.randint(1, 3))
                        grade_approved_at = approve_date.strftime('%Y-%m-%d %H:%M:%S')
                        grade_approved_by = admin_id
                        grade_submission_note = 'All grades completed and verified'
                        grade_approval_note = 'Approved - grades are accurate'
                        grade_workflow_stats['approved'] += 1
                    
                    elif is_current:
                        # For summer 2024-2025, most courses should be in draft or pending status
                        if is_summer_2024_2025:
                            rand = random.random()
                            if rand < 0.50:
                                grade_submission_status = 'draft'
                                grade_workflow_stats['draft'] += 1
                            elif rand < 0.80:
                                grade_submission_status = 'pending'
                                submit_date = datetime.now() - timedelta(days=random.randint(1, 5))
                                grade_submitted_at = submit_date.strftime('%Y-%m-%d %H:%M:%S')
                                grade_submission_note = 'Midterm grades ready for review'
                                grade_workflow_stats['pending'] += 1
                            else:
                                grade_submission_status = 'approved'
                                submit_date = datetime.now() - timedelta(days=random.randint(10, 20))
                                grade_submitted_at = submit_date.strftime('%Y-%m-%d %H:%M:%S')
                                approve_date = submit_date + timedelta(days=random.randint(1, 3))
                                grade_approved_at = approve_date.strftime('%Y-%m-%d %H:%M:%S')
                                grade_approved_by = admin_id
                                grade_submission_note = 'Early submission'
                                grade_approval_note = 'Approved - verified'
                                grade_workflow_stats['approved'] += 1
                        else:
                            # Fall 2025
                            rand = random.random()
                            if rand < 0.40:
                                grade_submission_status = 'draft'
                                grade_workflow_stats['draft'] += 1
                            elif rand < 0.70:
                                grade_submission_status = 'pending'
                                submit_date = datetime.now() - timedelta(days=random.randint(1, 5))
                                grade_submitted_at = submit_date.strftime('%Y-%m-%d %H:%M:%S')
                                grade_submission_note = 'Midterm grades ready for review'
                                grade_workflow_stats['pending'] += 1
                            else:
                                grade_submission_status = 'approved'
                                submit_date = datetime.now() - timedelta(days=random.randint(10, 20))
                                grade_submitted_at = submit_date.strftime('%Y-%m-%d %H:%M:%S')
                                approve_date = submit_date + timedelta(days=random.randint(1, 3))
                                grade_approved_at = approve_date.strftime('%Y-%m-%d %H:%M:%S')
                                grade_approved_by = admin_id
                                grade_submission_note = 'Early midterm submission'
                                grade_approval_note = 'Approved - early submission verified'
                                grade_workflow_stats['approved'] += 1
                    
                    # Store metadata
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
                        'max_students': session_max_students,
                        'session_number': session_idx + 1,
                        'enrolled_count': 0,  # Will be updated during enrollment
                        'grade_submission_status': grade_submission_status,
                        'grade_submitted_at': grade_submitted_at,
                        'grade_approved_at': grade_approved_at,
                        'grade_approved_by': grade_approved_by,
                        'grade_submission_note': grade_submission_note,
                        'grade_approval_note': grade_approval_note
                    })
                    
                    course_class_rows.append([
                        course_class_id,
                        course['course_id'],
                        instructor_id,
                        room['room_id'],
                        actual_start_date,
                        course_end_date,
                        session_max_students,
                        days[0],
                        time_slot[0],
                        time_slot[1],
                        'active',
                        grade_submission_status,
                        grade_submitted_at,
                        grade_approved_at,
                        grade_approved_by,
                        grade_submission_note,
                        grade_approval_note
                    ])
                    
                    sections_created += 1
                    scheduled = True
            
            if not scheduled:
                sections_skipped += 1
                self.add_statement(f"-- SKIPPED: {course['subject_code']} section {session_idx+1} (no conflict-free slot)")
    
    self.add_statement(f"\n-- Courses with no student demand: {courses_with_no_demand}")
    self.add_statement(f"-- Sections created: {sections_created}")
    self.add_statement(f"-- Sections skipped (conflicts): {sections_skipped}")
    self.add_statement(f"-- Grade workflow distribution:")
    self.add_statement(f"--   Approved: {grade_workflow_stats['approved']}")
    self.add_statement(f"--   Pending: {grade_workflow_stats['pending']}")
    self.add_statement(f"--   Draft: {grade_workflow_stats['draft']}")
    self.add_statement(f"-- NOTE: Course classes are created for:")
    self.add_statement(f"--       - Past semesters (start_year < 2025)")
    self.add_statement(f"--       - Fall 2025 (start_year == 2025, semester_type == 'fall') - CURRENT registration period")
    self.add_statement(f"--       Future semesters (Spring/Summer 2025, 2026+) are NOT opened for registration")
    
    self.bulk_insert('course_class', 
                    ['course_class_id', 'course_id', 'instructor_id', 'room_id', 'date_start', 'date_end', 
                    'max_students', 'day_of_week', 'start_period', 'end_period', 'course_class_status',
                    'grade_submission_status', 'grade_submitted_at', 'grade_approved_at', 'grade_approved_by',
                    'grade_submission_note', 'grade_approval_note'],
                    course_class_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_courses = create_courses
SQLDataGenerator.create_course_classes = create_course_classes