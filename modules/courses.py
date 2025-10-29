import random
from collections import defaultdict
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


from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_courses = create_courses
SQLDataGenerator.create_course_classes = create_course_classes