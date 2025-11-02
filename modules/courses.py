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
    self.add_statement("\n-- ==================== COURSE CLASSES (WITH GRADE SUBMISSION WORKFLOW) ====================")
    self.add_statement("-- Each course_class has grade submission status tracking")
    self.add_statement("-- Past courses: approved grades | Current courses: draft/pending grades")
    
    course_class_rows = []
    
    # Get admin user for grade approval
    admin_id = self.data['fixed_accounts']['admin']['admin_id']
    
    # Calculate students per course to determine number of class sessions needed
    # FIXED: Use curriculum_details instead of cls['curriculum']
    course_student_counts = defaultdict(set)
    for student in self.data['students']:
        class_id = student['class_id']
        cls = next((c for c in self.data['classes'] if c['class_id'] == class_id), None)
        if not cls:
            continue
        
        # Get curriculum_id from class
        curriculum_id = cls.get('curriculum_id')
        if not curriculum_id:
            continue
        
        # Get all subjects in this curriculum
        curriculum_subject_ids = set()
        for cd in self.data.get('curriculum_details', []):
            if cd['curriculum_id'] == curriculum_id:
                curriculum_subject_ids.add(cd['subject_id'])
        
        if not curriculum_subject_ids:
            continue
        
        # Match courses that teach these subjects
        for course in self.data['courses']:
            if course['subject_id'] in curriculum_subject_ids:
                if course['start_year'] >= student['class_start_year']:
                    course_student_counts[course['course_id']].add(student['student_id'])
    
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
        (1, 3),    # 7:00-9:30
        (4, 6),    # 9:45-12:15
        (7, 9),    # 13:00-15:30
        (10, 12),  # 15:45-18:15
    ]
    
    room_usage = {}
    
    grade_workflow_stats = {
        'approved': 0,
        'pending': 0,
        'draft': 0
    }
    
    for course in self.data['courses']:
        total_hours = course['theory_hours'] + course['practice_hours']
        if total_hours == 0:
            continue
        
        num_students = len(course_student_counts.get(course['course_id'], set()))
        if num_students == 0:
            continue
        
        max_per_session = 50
        num_sessions = max(1, (num_students + max_per_session - 1) // max_per_session)
        
        for session_idx in range(num_sessions):
            scheduled = False
            attempts = 0
            max_attempts = 100
            
            # Select instructor
            if course['start_year'] == 2025 and course['semester_type'] == 'fall' and random.random() < 0.3:
                instructor_id = self.data['fixed_accounts']['instructor']['instructor_id']
            else:
                instructor_id = random.choice(self.data['instructors'])['instructor_id']
            
            while not scheduled and attempts < max_attempts:
                attempts += 1
                
                room = random.choice(self.data['rooms'])
                days = random.choice(day_combinations)
                time_slot = random.choice(time_slots)
                
                conflict = False
                for day in days:
                    for period in range(time_slot[0], time_slot[1] + 1):
                        if (room['room_id'], day, period) in room_usage:
                            conflict = True
                            break
                    if conflict:
                        break
                
                if not conflict:
                    course_class_id = self.generate_uuid()
                    
                    for day in days:
                        for period in range(time_slot[0], time_slot[1] + 1):
                            room_usage[(room['room_id'], day, period)] = course_class_id
                    
                    # Determine grade submission status based on semester
                    is_past = (course['start_year'] < 2025) or \
                             (course['start_year'] == 2025 and course['semester_type'] == 'spring')
                    is_current = (course['start_year'] == 2025 and course['semester_type'] == 'fall')
                    
                    # Initialize grade workflow fields
                    grade_submission_status = 'draft'
                    grade_submitted_at = None
                    grade_approved_at = None
                    grade_approved_by = None
                    grade_submission_note = None
                    grade_approval_note = None
                    
                    if is_past:
                        # Past courses: All grades approved
                        grade_submission_status = 'approved'
                        semester_end_date = course['semester_end']
                        if isinstance(semester_end_date, str):
                            semester_end_date = datetime.strptime(semester_end_date, '%Y-%m-%d').date()
                        submit_date = datetime.combine(semester_end_date, datetime.min.time()) - timedelta(days=random.randint(3, 7))
                        grade_submitted_at = submit_date.strftime('%Y-%m-%d %H:%M:%S')
                        approve_date = submit_date + timedelta(days=random.randint(1, 3))
                        grade_approved_at = approve_date.strftime('%Y-%m-%d %H:%M:%S')
                        grade_approved_by = admin_id
                        grade_submission_note = random.choice([
                            'All grades completed and verified',
                            'Grade submission for final approval',
                            'Ready for administrative review'
                        ])
                        grade_approval_note = random.choice([
                            'Approved - grades are accurate',
                            'Verified and approved',
                            'All grades validated and approved'
                        ])
                        grade_workflow_stats['approved'] += 1
                    
                    elif is_current:
                        rand = random.random()
                        if rand < 0.40:
                            grade_submission_status = 'draft'
                            grade_workflow_stats['draft'] += 1
                        elif rand < 0.70:
                            grade_submission_status = 'pending'
                            submit_date = datetime.now() - timedelta(days=random.randint(1, 5))
                            grade_submitted_at = submit_date.strftime('%Y-%m-%d %H:%M:%S')
                            grade_submission_note = random.choice([
                                'Midterm grades ready for review',
                                'Submitting current grades for approval',
                                'Please review and approve grades'
                            ])
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
                        'max_students': max_per_session,
                        'session_number': session_idx + 1,
                        'enrolled_count': 0,
                        'grade_submission_status': grade_submission_status,
                        'grade_submitted_at': grade_submitted_at,
                        'grade_approved_at': grade_approved_at,
                        'grade_approved_by': grade_approved_by
                    })
                    
                    course_class_rows.append([
                        course_class_id,
                        course['course_id'],
                        instructor_id,
                        room['room_id'],
                        course['semester_start'],
                        course['semester_end'],
                        max_per_session,
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
                    
                    scheduled = True
            
            if not scheduled:
                # Fallback
                course_class_id = self.generate_uuid()
                room = random.choice(self.data['rooms'])
                days = random.choice(day_combinations)
                time_slot = random.choice(time_slots)
                
                is_past = (course['start_year'] < 2025) or \
                         (course['start_year'] == 2025 and course['semester_type'] == 'spring')
                
                grade_submission_status = 'approved' if is_past else 'draft'
                grade_submitted_at = None
                grade_approved_at = None
                grade_approved_by = None
                grade_submission_note = None
                grade_approval_note = None
                
                if is_past:
                    semester_end_date = course['semester_end']
                    if isinstance(semester_end_date, str):
                        semester_end_date = datetime.strptime(semester_end_date, '%Y-%m-%d').date()
                    submit_date = datetime.combine(semester_end_date, datetime.min.time()) - timedelta(days=5)
                    grade_submitted_at = submit_date.strftime('%Y-%m-%d %H:%M:%S')
                    approve_date = submit_date + timedelta(days=2)
                    grade_approved_at = approve_date.strftime('%Y-%m-%d %H:%M:%S')
                    grade_approved_by = admin_id
                    grade_submission_note = 'Grade submission for approval'
                    grade_approval_note = 'Approved'
                
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
                    'enrolled_count': 0,
                    'grade_submission_status': grade_submission_status,
                    'grade_submitted_at': grade_submitted_at,
                    'grade_approved_at': grade_approved_at,
                    'grade_approved_by': grade_approved_by
                })
                
                course_class_rows.append([
                    course_class_id,
                    course['course_id'],
                    instructor_id,
                    room['room_id'],
                    course['semester_start'],
                    course['semester_end'],
                    max_per_session,
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
                
                self.add_statement(f"-- WARNING: Could not find conflict-free slot for {course['subject_code']} session {session_idx+1}")
    
    self.add_statement(f"\n-- Generated {len(self.data['course_classes'])} course class sections")
    self.add_statement(f"-- Grade workflow status distribution:")
    self.add_statement(f"--   Approved: {grade_workflow_stats['approved']}")
    self.add_statement(f"--   Pending: {grade_workflow_stats['pending']}")
    self.add_statement(f"--   Draft: {grade_workflow_stats['draft']}")
    
    self.bulk_insert('course_class', 
                    ['course_class_id', 'course_id', 'instructor_id', 'room_id', 'date_start', 'date_end', 
                    'max_students', 'day_of_week', 'start_period', 'end_period', 'course_class_status',
                    'grade_submission_status', 'grade_submitted_at', 'grade_approved_at', 'grade_approved_by',
                    'grade_submission_note', 'grade_approval_note'],
                    course_class_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_courses = create_courses
SQLDataGenerator.create_course_classes = create_course_classes