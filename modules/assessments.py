import random
from datetime import datetime, timedelta
from collections import defaultdict
from .config import *

def create_exams_and_exam_entries(self):
    """
    UPDATED: Generate exam definitions and exam entries
    - exam: course-level exam definition (with notes column)
    - exam_entry: instructor-submitted exam PDFs (pending/approved/rejected, with codes)
    - exam_class: specific exam schedule for a course_class
    """
    self.add_statement("\n-- ==================== EXAMS, EXAM ENTRIES & EXAM CLASSES ====================")
    self.add_statement("-- exam: course-level exam definition")
    self.add_statement("-- exam_entry: instructor submissions (PDFs, approval workflow)")
    self.add_statement("-- exam_class: specific exam schedule with room and time")
    
    exam_rows = []
    exam_entry_rows = []
    exam_class_rows = []
    
    # Initialize storage for exam_classes
    self.data['exam_classes'] = []
    
    # Track created exams by course_id to avoid duplicates
    exams_by_course = {}
    
    # GLOBAL: Track room usage across ALL courses to prevent conflicts
    # Key: (room_id, date_str, hour, minute) -> True
    global_exam_room_usage = {}
    
    # Group course_classes by course
    course_classes_by_course = defaultdict(list)
    for cc in self.data['course_classes']:
        course_classes_by_course[cc['course_id']].append(cc)
    
    # Get admin for reviewing exam entries
    admin_id = self.data['fixed_accounts']['admin']['admin_id']
    
    # Exam notes templates (for the exam.notes column)
    exam_notes_templates = [
        'Sinh viên cần mang theo CMND/CCCD và thẻ sinh viên',
        'Sinh viên được phép sử dụng máy tính cá nhân',
        'Không được mang tài liệu vào phòng thi',
        'Sinh viên cần đến trước 15 phút',
        'Sinh viên được sử dụng tài liệu mở',
        'Bài thi thực hành trên máy tính',
        'Sinh viên cần chuẩn bị giấy nháp',
        'Không được sử dụng điện thoại trong phòng thi',
        'Sinh viên làm bài trên giấy thi phát',
        'Bài thi có thời gian 120 phút',
        'Sinh viên nghỉ có phép cần liên hệ phòng đào tạo',
        'Sinh viên vi phạm quy chế thi sẽ bị xử lý kỷ luật',
        'Mang theo bút viết, tẩy, thước kẻ',
        'Bài thi không được tẩy xóa',
        'Nộp bài trước 30 phút cuối có thể rời phòng thi',
    ]
    
    for course_id, course_classes in course_classes_by_course.items():
        course = next((c for c in self.data['courses'] if c['course_id'] == course_id), None)
        if not course:
            continue
            
        # Skip if this course already has an exam (prevent duplicates)
        if course_id in exams_by_course:
            continue
        
        # ============================================================
        # 1. CREATE EXAM DEFINITION (once per course)
        # ============================================================
        exam_id = self.generate_uuid()
        exam_format = random.choice(['multiple_choice', 'essay', 'practical', 'oral', 'mixed'])
        exam_type = random.choice(['midterm', 'final', 'final', 'final'])  # More finals
        
        # Determine how many exam codes needed (typically 2-4 variants)
        num_exam_codes_needed = random.randint(2, 4)
        
        # Generate exam notes (60% chance to have notes)
        exam_notes = None
        if random.random() < 0.80:
            # Pick 1-3 random note templates
            num_notes = random.randint(1, 3)
            selected_notes = random.sample(exam_notes_templates, num_notes)
            exam_notes = '. '.join(selected_notes) + '.'
        
        exam_rows.append([
            exam_id,
            course_id,
            exam_format,
            exam_type,
            exam_notes,  # Single notes column
            num_exam_codes_needed,
            'published'  # Assume published for demo
        ])
        
        exams_by_course[course_id] = exam_id
        
        # ============================================================
        # 2. CREATE EXAM ENTRIES (instructor submissions)
        # ============================================================
        # Each course_class instructor submits their exam version
        submitted_entries = []
        
        for cc in course_classes:
            if random.random() < 0.6:
                exam_entry_id = self.generate_uuid()
                
                # Display name (instructor's submission identifier)
                instructor = next((i for i in self.data['instructors'] 
                                if i['instructor_id'] == cc['instructor_id']), None)
                instructor_name = instructor['full_name'] if instructor else 'GV'
                display_name = f"{course['subject_code']} - {instructor_name} - Lớp {cc['session_number']}"
                
                # Get random exam PDF and answer key
                question_pdf = self.media_scanner.get_random_file('course_docs', 'pdf')
                answer_pdf = self.media_scanner.get_random_file('course_docs', 'pdf')
                
                question_file_path = self.media_scanner.build_url('exams', question_pdf)
                answer_file_path = self.media_scanner.build_url('exams', answer_pdf)
                
                # Duration
                duration_minutes = random.choice([90, 120, 150, 180])
                
                # Approval status (80% approved, 15% pending, 5% rejected)
                status_rand = random.random()
                if status_rand < 0.80:
                    entry_status = 'approved'
                    is_picked = False  # Will be set to True for selected entries later
                    entry_code = None
                    rejection_reason = None
                    reviewed_by = admin_id
                    reviewed_at = datetime.now() - timedelta(days=random.randint(5, 30))
                elif status_rand < 0.95:
                    entry_status = 'pending'
                    is_picked = False
                    entry_code = None
                    rejection_reason = None
                    reviewed_by = None
                    reviewed_at = None
                else:
                    entry_status = 'rejected'
                    is_picked = False
                    entry_code = None
                    rejection_reason = random.choice([
                        'Đề thi không đúng format',
                        'Thiếu đáp án',
                        'Độ khó chưa phù hợp',
                        'Cần bổ sung câu hỏi'
                    ])
                    reviewed_by = admin_id
                    reviewed_at = datetime.now() - timedelta(days=random.randint(1, 15))
                
                exam_entry_rows.append([
                    exam_entry_id,
                    exam_id,
                    cc['course_class_id'],
                    entry_code,  # Will be updated for picked entries
                    display_name,
                    question_file_path,
                    answer_file_path,
                    duration_minutes,
                    is_picked,
                    entry_status,
                    rejection_reason,
                    reviewed_by,
                    reviewed_at
                ])
                
                if entry_status == 'approved':
                    submitted_entries.append({
                        'exam_entry_id': exam_entry_id,
                        'course_class_id': cc['course_class_id'],
                        'duration_minutes': duration_minutes
                    })
        
        # ============================================================
        # 3. PICK EXAM ENTRIES (assign entry codes A, B, C, etc.)
        # ============================================================
        # Randomly select entries up to num_exam_codes_needed
        if submitted_entries:
            num_to_pick = min(num_exam_codes_needed, len(submitted_entries))
            picked_entries = random.sample(submitted_entries, num_to_pick)
            
            entry_codes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            
            for idx, entry in enumerate(picked_entries):
                entry_code = entry_codes[idx] if idx < len(entry_codes) else f"E{idx+1}"
                
                # UPDATE the exam_entry row to mark it as picked with entry_code
                # Find the row in exam_entry_rows
                for i, row in enumerate(exam_entry_rows):
                    if row[0] == entry['exam_entry_id']:  # exam_entry_id match
                        # Update entry_code (index 3) and is_picked (index 8)
                        exam_entry_rows[i][3] = entry_code
                        exam_entry_rows[i][8] = True  # is_picked
                        break
        
        # ============================================================
        # 4. CREATE EXAM_CLASS SCHEDULES
        # ============================================================
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
        
        # Use GLOBAL room usage tracking to prevent conflicts across all courses
        # (not local to this course group)
        
        for cc in course_classes:
            # Try to schedule exam without conflicts
            exam_scheduled = False
            
            for attempt in range(50):  # Increased attempts
                exam_date = random.choice(exam_dates)
                hour, minute, duration = random.choice(exam_slots)
                start_time = datetime.combine(exam_date, datetime.min.time().replace(hour=hour, minute=minute))
                room = random.choice(self.data['rooms'])
                
                # Create conflict check key: room + date + time slot
                date_str = exam_date.strftime('%Y-%m-%d')
                key = (room['room_id'], date_str, hour, minute)
                
                # Check for room conflicts (same room, same date, overlapping time)
                room_conflict = False
                
                # Simple check: if exact same room, date, hour, minute already exists, it's a conflict
                if key in global_exam_room_usage:
                    room_conflict = True
                else:
                    # Check for time overlap (2-hour slots)
                    for existing_key in global_exam_room_usage:
                        existing_room, existing_date, existing_hour, existing_minute = existing_key
                        if (existing_room == room['room_id'] and 
                            existing_date == date_str):
                            
                            existing_start_minutes = existing_hour * 60 + existing_minute
                            existing_end_minutes = existing_start_minutes + 120  # 2 hours
                            current_start_minutes = hour * 60 + minute
                            current_end_minutes = current_start_minutes + 120
                            
                            # Check overlap
                            if not (current_end_minutes <= existing_start_minutes or 
                                   current_start_minutes >= existing_end_minutes):
                                room_conflict = True
                                break
                
                if not room_conflict:
                    # Try to find an instructor who doesn't have conflicts
                    monitor_instructor = None
                    
                    # Shuffle the instructor list to get variety
                    potential_instructors = list(self.data['instructors'])
                    random.shuffle(potential_instructors)
                    
                    for potential_instructor in potential_instructors:
                        instructor_id = potential_instructor['instructor_id']
                        
                        # Check if this instructor has course classes at the same time
                        instructor_conflict = False
                        exam_weekday = exam_date.weekday() + 2  # Convert to 1-7 (Monday=2, Tuesday=3, etc.)
                        
                        for course_class in self.data['course_classes']:
                            if course_class['instructor_id'] == instructor_id:
                                # Check if course class is in the same semester and has overlapping time
                                cc_days = course_class.get('days', [])
                                if exam_weekday in cc_days:
                                    cc_start = course_class.get('start_period', 0)
                                    cc_end = course_class.get('end_period', 0)
                                    
                                    # Convert exam time to periods more accurately
                                    # Period 1 = 6:00-7:00, Period 2 = 7:00-8:00, etc.
                                    # So 7:30 AM = Period 2, 13:30 PM = Period 8
                                    if hour <= 6:
                                        exam_start_period = 1
                                    elif hour <= 12:
                                        exam_start_period = hour - 5  # 7:00 AM = Period 2
                                    else:
                                        exam_start_period = hour - 5  # 13:00 PM = Period 8
                                    
                                    exam_end_period = exam_start_period + 1  # 2-hour exam = 2 periods
                                    
                                    # Check for period overlap
                                    if not (exam_end_period <= cc_start or exam_start_period >= cc_end):
                                        instructor_conflict = True
                                        break
                        
                        if not instructor_conflict:
                            monitor_instructor = potential_instructor
                            break
                    
                    if monitor_instructor is None:
                        # Fallback: use any instructor if no conflict-free one found
                        # But prefer someone who's NOT the test instructor to avoid conflicts
                        test_instructor_id = self.data['fixed_accounts'].get('instructor', {}).get('instructor_id')
                        available_instructors = [
                            instr for instr in self.data['instructors']
                            if instr['instructor_id'] != test_instructor_id
                        ]
                        if available_instructors:
                            monitor_instructor = random.choice(available_instructors)
                        else:
                            monitor_instructor = random.choice(self.data['instructors'])
                    
                    global_exam_room_usage[key] = True
                    
                    exam_class_id = self.generate_uuid()
                    
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
                    
                    # Store in self.data for potential future use
                    self.data['exam_classes'].append({
                        'exam_class_id': exam_class_id,
                        'exam_id': exam_id,
                        'course_class_id': cc['course_class_id'],
                        'room_id': room['room_id'],
                        'start_time': start_time
                    })
                    
                    exam_scheduled = True
                    break
            
            if not exam_scheduled:
                # Fallback: try different room and time combinations more systematically
                fallback_scheduled = False
                for backup_room in self.data['rooms']:
                    if fallback_scheduled:
                        break
                    for backup_date in exam_dates:
                        if fallback_scheduled:
                            break
                        for backup_hour, backup_minute, backup_duration in exam_slots:
                            backup_start_time = datetime.combine(backup_date, datetime.min.time().replace(hour=backup_hour, minute=backup_minute))
                            
                            # Check for conflicts with this backup combination
                            backup_date_str = backup_date.strftime('%Y-%m-%d')
                            backup_key = (backup_room['room_id'], backup_date_str, backup_hour, backup_minute)
                            
                            backup_conflict = False
                            for existing_key in global_exam_room_usage:
                                existing_room, existing_date, existing_hour, existing_minute = existing_key
                                if (existing_room == backup_room['room_id'] and 
                                    existing_date == backup_date_str):
                                    # Check for time overlap
                                    existing_start_minutes = existing_hour * 60 + existing_minute
                                    existing_end_minutes = existing_start_minutes + 120
                                    backup_start_minutes = backup_hour * 60 + backup_minute
                                    backup_end_minutes = backup_start_minutes + 120
                                    
                                    if not (backup_end_minutes <= existing_start_minutes or 
                                           backup_start_minutes >= existing_end_minutes):
                                        backup_conflict = True
                                        break
                            
                            if not backup_conflict:
                                # Try to find an instructor who doesn't have conflicts for fallback
                                monitor_instructor = None
                                for potential_instructor in self.data['instructors']:
                                    instructor_id = potential_instructor['instructor_id']
                                    
                                    # Check if this instructor has course classes at the same time
                                    instructor_conflict = False
                                    backup_weekday = backup_date.weekday() + 1  # Convert to 1-7 (Monday=1)
                                    
                                    for course_class in self.data['course_classes']:
                                        if course_class['instructor_id'] == instructor_id:
                                            # Check if course class is in the same semester and has overlapping time
                                            cc_days = course_class.get('days', [])
                                            if backup_weekday in cc_days:
                                                cc_start = course_class.get('start_period', 0)
                                                cc_end = course_class.get('end_period', 0)
                                                
                                                # Convert exam time to periods (approximately)
                                                exam_period = backup_hour - 6  # Rough conversion: 7:00 AM = period 1
                                                exam_end_period = exam_period + 2  # 2-hour exam
                                                
                                                # Check for period overlap
                                                if not (exam_end_period <= cc_start or exam_period >= cc_end):
                                                    instructor_conflict = True
                                                    break
                                    
                                    if not instructor_conflict:
                                        monitor_instructor = potential_instructor
                                        break
                                
                                if monitor_instructor is None:
                                    # Fallback: use any instructor if no conflict-free one found
                                    monitor_instructor = random.choice(self.data['instructors'])
                                
                                global_exam_room_usage[backup_key] = True
                                
                                exam_class_id = self.generate_uuid()
                                
                                exam_class_rows.append([
                                    exam_class_id,
                                    exam_id,
                                    cc['course_class_id'],
                                    backup_room['room_id'],
                                    monitor_instructor['instructor_id'],
                                    backup_start_time,
                                    backup_duration,
                                    'scheduled'
                                ])
                                
                                self.data['exam_classes'].append({
                                    'exam_class_id': exam_class_id,
                                    'exam_id': exam_id,
                                    'course_class_id': cc['course_class_id'],
                                    'room_id': backup_room['room_id'],
                                    'start_time': backup_start_time
                                })
                                
                                fallback_scheduled = True
                                break
                
                # If still not scheduled, skip this exam to avoid conflicts
                if not fallback_scheduled:
                    self.add_statement(f"-- WARNING: Could not schedule exam for course_class {cc['course_class_id']} without conflicts")
    
    # SPECIAL HANDLING FOR ALL TEST STUDENTS: Create exam schedules for summer 2024-2025 courses
    # with specific dates: 2 exams on 11/6 (completed), 2 on 11/12 (upcoming), 2 on 11/19 (scheduled)
    # Process each test student
    for account_name, account_data in self.data.get('fixed_accounts', {}).items():
        if not account_name.startswith('student'):
            continue
        test_student_id = account_data.get('student_id')
        if not test_student_id:
            continue
        from datetime import date
        TODAY = datetime.now().date()
        
        # Calculate exam dates relative to TODAY (November 12, 2025)
        # REQUIREMENTS: 
        # - 2 exams already done (past dates) 
        # - 2 exams upcoming (within 7 days from today)
        # - 2 exams in far future (beyond 7 days from today)
        
        # Past exams: 3 and 5 days ago (completed)
        exam_date_past_1 = TODAY - timedelta(days=3)      # Nov 9, 2025
        exam_date_past_2 = TODAY - timedelta(days=5)      # Nov 7, 2025
        
        # Near future exams: 2 and 4 days from today (upcoming, within 7 days)
        exam_date_upcoming_1 = TODAY + timedelta(days=2)  # Nov 14, 2025
        exam_date_upcoming_2 = TODAY + timedelta(days=4)  # Nov 16, 2025
        
        # Far future exams: 10 and 12 days from today (beyond 7 days)
        exam_date_future_1 = TODAY + timedelta(days=10)   # Nov 22, 2025
        exam_date_future_2 = TODAY + timedelta(days=12)   # Nov 24, 2025
        
        # Find summer 2024-2025 semester
        # Summer 2024-2025: academic year is 2024-2025 (start_year=2024, end_year=2025)
        # and ends in November 2025 (end_date month is 11)
        summer_2024_2025_semester = None
        for sem in self.data['semesters']:
            if sem['semester_type'] == 'summer':
                # Check if this is summer 2024-2025: academic year 2024-2025
                if sem.get('start_year') == 2024 and sem.get('end_year') == 2025:
                    # Also verify end date is in November 2025
                    sem_end = sem['end_date']
                    if isinstance(sem_end, str):
                        from datetime import datetime as dt
                        sem_end = dt.strptime(sem_end, '%Y-%m-%d').date()
                    if sem_end.year == 2025 and sem_end.month == 11:
                        summer_2024_2025_semester = sem
                        break
        
        if summer_2024_2025_semester:
            # Get test student's enrollments in summer 2024-2025
            test_student_summer_enrollments = [
                e for e in self.data['enrollments'] 
                if e['student_id'] == test_student_id 
                and e['semester_id'] == summer_2024_2025_semester['semester_id']
            ]
            
            # Get course classes for these enrollments
            test_student_course_classes = []
            for enrollment in test_student_summer_enrollments:
                cc = next((c for c in self.data['course_classes'] 
                          if c['course_class_id'] == enrollment['course_class_id']), None)
                if cc:
                    test_student_course_classes.append(cc)
            
            # Remove existing exam_class entries for test student's courses (to override normal exam creation)
            test_student_course_class_ids = {cc['course_class_id'] for cc in test_student_course_classes}
            
            # Remove exam_class entries that were already created for these course classes
            exam_class_rows_to_remove = []
            self.data_exam_classes_to_remove = []
            
            for i in range(len(exam_class_rows) - 1, -1, -1):
                if exam_class_rows[i][2] in test_student_course_class_ids:  # course_class_id is at index 2
                    exam_class_rows_to_remove.append(exam_class_rows.pop(i))
            
            # Also remove from self.data['exam_classes']
            for i in range(len(self.data['exam_classes']) - 1, -1, -1):
                if self.data['exam_classes'][i]['course_class_id'] in test_student_course_class_ids:
                    self.data_exam_classes_to_remove.append(self.data['exam_classes'].pop(i))
            
            if exam_class_rows_to_remove:
                self.add_statement(f"-- TEST STUDENT: Removed {len(exam_class_rows_to_remove)} existing exam_class entries to override with specific dates")
            
            # Note: We do NOT clear global_exam_room_usage here because we want to respect existing conflicts
            # The test student logic will find available time slots that don't conflict with regular exams
            
            # Work with available course classes (even if less than 6, we'll still create exams)
            # But try to ensure we have at least 6 enrollments
            if len(test_student_course_classes) < 6:
                self.add_statement(f"-- WARNING: Test student only has {len(test_student_course_classes)} enrollments in summer 2024-2025, expected 6")
            
            if len(test_student_course_classes) > 0:
                # Get courses for these course classes
                test_student_courses = []
                # Take up to 6 courses (or all if less than 6)
                num_courses_to_use = min(6, len(test_student_course_classes))
                for cc in test_student_course_classes[:num_courses_to_use]:
                    course = next((c for c in self.data['courses'] 
                                 if c['course_id'] == cc['course_id']), None)
                    if course:
                        test_student_courses.append({
                            'course': course,
                            'course_class': cc
                        })
                
                # Assign exam dates: distribute across past, upcoming, future
                # FIXED DISTRIBUTION: Ensure exactly 2 exams in each period
                num_courses = len(test_student_courses)
                if num_courses >= 6:
                    # 6 courses: 2 past + 2 upcoming + 2 future
                    exam_date_assignments = [
                        (exam_date_past_1, 1),      # 1 exam 3 days ago
                        (exam_date_past_2, 1),      # 1 exam 5 days ago  
                        (exam_date_upcoming_1, 1),  # 1 exam in 2 days
                        (exam_date_upcoming_2, 1),  # 1 exam in 4 days
                        (exam_date_future_1, 1),    # 1 exam in 10 days
                        (exam_date_future_2, 1),    # 1 exam in 12 days
                    ]
                elif num_courses == 5:
                    # 5 courses: 2 past + 2 upcoming + 1 future  
                    exam_date_assignments = [
                        (exam_date_past_1, 1),      # 1 exam in past
                        (exam_date_past_2, 1),      # 1 exam in past
                        (exam_date_upcoming_1, 1),  # 1 exam upcoming
                        (exam_date_upcoming_2, 1),  # 1 exam upcoming
                        (exam_date_future_1, 1),    # 1 exam future
                    ]
                elif num_courses == 4:
                    # 4 courses: 1 past + 2 upcoming + 1 future
                    exam_date_assignments = [
                        (exam_date_past_1, 1),      # 1 exam in past
                        (exam_date_upcoming_1, 1),  # 1 exam upcoming
                        (exam_date_upcoming_2, 1),  # 1 exam upcoming
                        (exam_date_future_1, 1),    # 1 exam future
                    ]
                else:
                    # Less than 4 courses: distribute as evenly as possible
                    exam_date_assignments = [
                        (exam_date_past_1, min(1, num_courses)),
                        (exam_date_upcoming_1, min(1, max(0, num_courses - 1))),
                        (exam_date_future_1, min(1, max(0, num_courses - 2))),
                    ]
                    # Remove zero-count assignments
                    exam_date_assignments = [(date, count) for date, count in exam_date_assignments if count > 0]
                
                # Exam time slots: (hour, minute, duration_minutes)
                exam_slots = [
                    (7, 30, 120),   # 7:30 AM, 2 hours
                    (10, 0, 120),   # 10:00 AM, 2 hours
                    (13, 30, 120),  # 1:30 PM, 2 hours
                    (16, 0, 120),   # 4:00 PM, 2 hours
                ]
                
                # Track which time slots are used for each specific date to prevent conflicts
                # Each date gets its own tracking to ensure unique time slots
                date_slot_usage = {}
                for target_date in [exam_date_past_1, exam_date_past_2, exam_date_upcoming_1, 
                                   exam_date_upcoming_2, exam_date_future_1, exam_date_future_2]:
                    date_slot_usage[target_date.strftime('%Y-%m-%d')] = set()
                
                # Also track room usage per date+time to avoid double booking
                date_time_room_usage = {}
                
                course_idx = 0
                for exam_date, count in exam_date_assignments:
                    # Determine exam status based on date relative to TODAY
                    if exam_date < TODAY:
                        exam_status = 'completed'  # Already taken
                    else:
                        exam_status = 'scheduled'  # Upcoming or future
                    
                    exam_date_str = exam_date.strftime('%Y-%m-%d')
                    
                    for i in range(count):
                        if course_idx >= len(test_student_courses):
                            break
                        
                        course_info = test_student_courses[course_idx]
                        course = course_info['course']
                        cc = course_info['course_class']
                        
                        # Get or create exam for this course
                        exam_id = exams_by_course.get(course['course_id'])
                        if not exam_id:
                            # Create exam if it doesn't exist
                            exam_id = self.generate_uuid()
                            exam_format = random.choice(['multiple_choice', 'essay', 'practical', 'oral', 'mixed'])
                            exam_type = 'final'
                            num_exam_codes_needed = 2
                            
                            exam_notes = None
                            if random.random() < 0.80:
                                num_notes = random.randint(1, 3)
                                selected_notes = random.sample(exam_notes_templates, num_notes)
                                exam_notes = '. '.join(selected_notes) + '.'
                            
                            exam_rows.append([
                                exam_id,
                                course['course_id'],
                                exam_format,
                                exam_type,
                                exam_notes,
                                num_exam_codes_needed,
                                'published'
                            ])
                            
                            exams_by_course[course['course_id']] = exam_id
                        
                        # Create exam_entry if it doesn't exist
                        exam_entry_exists = any(
                            row[2] == cc['course_class_id'] for row in exam_entry_rows
                        )
                        
                        if not exam_entry_exists:
                            exam_entry_id = self.generate_uuid()
                            instructor = next((i for i in self.data['instructors'] 
                                            if i['instructor_id'] == cc['instructor_id']), None)
                            instructor_name = instructor['full_name'] if instructor else 'GV'
                            display_name = f"{course['subject_code']} - {instructor_name} - Lớp {cc.get('session_number', 1)}"
                            
                            question_pdf = self.media_scanner.get_random_file('course_docs', 'pdf')
                            answer_pdf = self.media_scanner.get_random_file('course_docs', 'pdf')
                            
                            question_file_path = self.media_scanner.build_url('exams', question_pdf)
                            answer_file_path = self.media_scanner.build_url('exams', answer_pdf)
                            
                            duration_minutes = random.choice([90, 120, 150, 180])
                            
                            exam_entry_rows.append([
                                exam_entry_id,
                                exam_id,
                                cc['course_class_id'],
                                'A',  # entry_code
                                display_name,
                                question_file_path,
                                answer_file_path,
                                duration_minutes,
                                True,  # is_picked
                                'approved',  # entry_status
                                None,  # rejection_reason
                                admin_id,  # reviewed_by
                                datetime.now() - timedelta(days=random.randint(5, 30))  # reviewed_at
                            ])
                        
                        # Find an available time slot for this specific date
                        exam_scheduled = False
                        
                        # Get already used slots for this date from our local tracking
                        used_slots_for_date = date_slot_usage[exam_date_str]
                        
                        # Shuffle slots to avoid always using the first one
                        slot_indices = list(range(len(exam_slots)))
                        random.shuffle(slot_indices)
                        
                        # Try to find an unused time slot
                        for slot_idx in slot_indices:
                            if slot_idx in used_slots_for_date:
                                continue  # This slot is already used for this date
                            
                            hour, minute, slot_duration = exam_slots[slot_idx]
                            
                            # Create unique key for this date+time combination (GLOBAL check)
                            date_time_key = f"{exam_date_str}_{hour:02d}_{minute:02d}"
                            
                            # STRICT: Skip if this exact date+time is already used by ANY student
                            if date_time_key in date_time_room_usage:
                                continue
                            
                            # Try different rooms for this time slot
                            available_rooms = [r for r in self.data['rooms'] if r.get('room_type') in ['exam', 'classroom', 'lecture_hall']]
                            if not available_rooms:
                                available_rooms = self.data['rooms']  # Fallback to all rooms
                            
                            # Shuffle rooms to get variety
                            random.shuffle(available_rooms)
                            
                            room_found = False
                            for room in available_rooms:
                                # Check if this room+date+time combination conflicts with global usage
                                conflict_key = (room['room_id'], exam_date_str, hour, minute)
                                
                                # Check for conflicts with global exam usage
                                room_conflict = False
                                
                                # Simple check: if exact same room, date, hour, minute already exists globally
                                if conflict_key in global_exam_room_usage:
                                    room_conflict = True
                                else:
                                    # Check for time overlap (2-hour slots) in global usage
                                    for existing_key in global_exam_room_usage:
                                        existing_room, existing_date, existing_hour, existing_minute = existing_key
                                        if (existing_room == room['room_id'] and 
                                            existing_date == exam_date_str):
                                            
                                            existing_start_minutes = existing_hour * 60 + existing_minute
                                            existing_end_minutes = existing_start_minutes + 120
                                            current_start_minutes = hour * 60 + minute
                                            current_end_minutes = current_start_minutes + 120
                                            
                                            # Check overlap
                                            if not (current_end_minutes <= existing_start_minutes or 
                                                   current_start_minutes >= existing_end_minutes):
                                                room_conflict = True
                                                break
                                
                                if not room_conflict:
                                    # Try to find an instructor who doesn't have conflicts
                                    monitor_instructor = None
                                    
                                    # Shuffle the instructor list to get variety
                                    potential_instructors = list(self.data['instructors'])
                                    random.shuffle(potential_instructors)
                                    
                                    for potential_instructor in potential_instructors:
                                        instructor_id = potential_instructor['instructor_id']
                                        
                                        # Check if this instructor has course classes at the same time
                                        instructor_conflict = False
                                        exam_weekday = exam_date.weekday() + 2  # Convert to 1-7 (Monday=2, Tuesday=3, etc.)
                                        
                                        for course_class in self.data['course_classes']:
                                            if course_class['instructor_id'] == instructor_id:
                                                # Check if course class is in the same semester and has overlapping time
                                                cc_days = course_class.get('days', [])
                                                if exam_weekday in cc_days:
                                                    cc_start = course_class.get('start_period', 0)
                                                    cc_end = course_class.get('end_period', 0)
                                                    
                                                    # Convert exam time to periods more accurately
                                                    # Period 1 = 6:00-7:00, Period 2 = 7:00-8:00, etc.
                                                    # So 7:30 AM = Period 2, 13:30 PM = Period 8
                                                    if hour <= 6:
                                                        exam_start_period = 1
                                                    elif hour <= 12:
                                                        exam_start_period = hour - 5  # 7:00 AM = Period 2
                                                    else:
                                                        exam_start_period = hour - 5  # 13:00 PM = Period 8
                                                    
                                                    exam_end_period = exam_start_period + 1  # 2-hour exam = 2 periods
                                                    
                                                    # Check for period overlap
                                                    if not (exam_end_period <= cc_start or exam_start_period >= cc_end):
                                                        instructor_conflict = True
                                                        break
                                        
                                        if not instructor_conflict:
                                            monitor_instructor = potential_instructor
                                            break
                                    
                                    if monitor_instructor is None:
                                        # Fallback: use any instructor if no conflict-free one found
                                        # But prefer someone who's NOT the test instructor to avoid conflicts
                                        test_instructor_id = self.data['fixed_accounts'].get('instructor', {}).get('instructor_id')
                                        available_instructors = [
                                            instr for instr in self.data['instructors']
                                            if instr['instructor_id'] != test_instructor_id
                                        ]
                                        if available_instructors:
                                            monitor_instructor = random.choice(available_instructors)
                                        else:
                                            monitor_instructor = random.choice(self.data['instructors'])
                                    
                                    # Found available slot, room, and instructor - now create exam
                                    exam_class_id = self.generate_uuid()
                                    
                                    # Mark this slot and date+time combination as used
                                    used_slots_for_date.add(slot_idx)
                                    date_time_room_usage[date_time_key] = room['room_id']
                                    global_exam_room_usage[conflict_key] = True
                                    
                                    exam_datetime = datetime.combine(exam_date, datetime.min.time().replace(hour=hour, minute=minute))
                                    
                                    exam_class_rows.append([
                                        exam_class_id,
                                        exam_id,
                                        cc['course_class_id'],
                                        room['room_id'],
                                        monitor_instructor['instructor_id'],
                                        exam_datetime,
                                        slot_duration,
                                        exam_status
                                    ])
                                    
                                    self.data['exam_classes'].append({
                                        'exam_class_id': exam_class_id,
                                        'exam_id': exam_id,
                                        'course_class_id': cc['course_class_id'],
                                        'room_id': room['room_id'],
                                        'start_time': exam_datetime
                                    })
                                    
                                    exam_scheduled = True
                                    room_found = True
                                    time_str = f"{hour:02d}:{minute:02d}"
                                    self.add_statement(f"-- TEST STUDENT: Exam scheduled for {course['subject_code']} on {exam_date} at {time_str} in {room.get('room_code', 'Room')} (status: {exam_status}) [Slot {slot_idx+1}]")
                                    break
                            
                            if room_found:
                                break
                        
                        if not exam_scheduled:
                            # Fallback: force schedule with any available room and unused slot
                            # Find any unused slot for this date
                            unused_slot_idx = None
                            for slot_idx in range(len(exam_slots)):
                                if slot_idx not in used_slots_for_date:
                                    unused_slot_idx = slot_idx
                                    break
                            
                            if unused_slot_idx is not None:
                                hour, minute, slot_duration = exam_slots[unused_slot_idx]
                                
                                # Try to find a room that doesn't conflict
                                available_rooms = list(self.data['rooms'])
                                random.shuffle(available_rooms)
                                
                                room = None
                                for candidate_room in available_rooms:
                                    fallback_key = (candidate_room['room_id'], exam_date_str, hour, minute)
                                    if fallback_key not in global_exam_room_usage:
                                        room = candidate_room
                                        break
                                
                                # If no conflict-free room found, use any room
                                if room is None:
                                    room = random.choice(available_rooms)
                                    fallback_key = (room['room_id'], exam_date_str, hour, minute)
                                
                                monitor_instructor = random.choice(self.data['instructors'])
                                
                                exam_class_id = self.generate_uuid()
                                exam_datetime = datetime.combine(exam_date, datetime.min.time().replace(hour=hour, minute=minute))
                                
                                # Mark slot and date+time as used
                                used_slots_for_date.add(unused_slot_idx)
                                date_time_key = f"{exam_date_str}_{hour:02d}_{minute:02d}"
                                date_time_room_usage[date_time_key] = room['room_id']
                                global_exam_room_usage[fallback_key] = True
                                
                                exam_class_rows.append([
                                    exam_class_id,
                                    exam_id,
                                    cc['course_class_id'],
                                    room['room_id'],
                                    monitor_instructor['instructor_id'],
                                    exam_datetime,
                                    slot_duration,
                                    exam_status
                                ])
                                
                                self.data['exam_classes'].append({
                                    'exam_class_id': exam_class_id,
                                    'exam_id': exam_id,
                                    'course_class_id': cc['course_class_id'],
                                    'room_id': room['room_id'],
                                    'start_time': exam_datetime
                                })
                                
                                time_str = f"{hour:02d}:{minute:02d}"
                                self.add_statement(f"-- TEST STUDENT: Exam scheduled (fallback) for {course['subject_code']} on {exam_date} at {time_str} (status: {exam_status}) [Slot {unused_slot_idx+1}]")
                            else:
                                # All slots for this date are used - this shouldn't happen with proper logic
                                self.add_statement(f"-- ERROR: Could not schedule exam for {course['subject_code']} on {exam_date} - all time slots used")
                        
                        course_idx += 1
                
                self.add_statement(f"-- TEST STUDENT: Created {course_idx} exam schedules for summer 2024-2025 courses")
                self.add_statement(f"-- DISTRIBUTION: 2 past exams, 2 near future (next week), 2 far future (beyond 1 week)")
    
    self.add_statement(f"-- Total exams (course-level): {len(exam_rows)}")
    self.add_statement(f"-- Total exam entries (instructor submissions): {len(exam_entry_rows)}")
    self.add_statement(f"-- Total exam_class (scheduled): {len(exam_class_rows)}")
    
    # Insert exam definitions
    self.bulk_insert('exam',
                    ['exam_id', 'course_id', 'exam_format', 'exam_type', 
                    'notes', 'num_exam_codes_needed', 'exam_status'],
                    exam_rows)
    
    # Insert exam entries
    self.bulk_insert('exam_entry',
                    ['exam_entry_id', 'exam_id', 'course_class_id', 'entry_code',
                    'display_name', 'question_file_path', 'answer_file_path',
                    'duration_minutes', 'is_picked', 'entry_status', 'rejection_reason',
                    'reviewed_by', 'reviewed_at'],
                    exam_entry_rows)
    
    # Insert exam_class schedules
    self.bulk_insert('exam_class',
                    ['exam_class_id', 'exam_id', 'course_class_id', 'room_id',
                    'monitor_instructor_id', 'start_time', 'duration_minutes', 'exam_status'],
                    exam_class_rows)


# Bind the function to SQLDataGenerator
from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_exams_and_exam_entries = create_exams_and_exam_entries