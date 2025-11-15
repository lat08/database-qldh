import random
from datetime import datetime, timedelta
from .config import *

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
    """Generate notifications targeted to different user groups"""
    self.add_statement("\n-- ==================== NOTIFICATIONS ====================")
    
    import random
    from datetime import datetime, timedelta
    
    notification_rows = []
    base_date = datetime.now()
    
    # Admin user ID for created_by_user
    admin_id = self.data['fixed_accounts']['admin']['user_id']
    
    # ============================================================
    # NOTICE MESSAGE TEMPLATES BY TYPE
    # ============================================================
    notice_messages = {
        'important': [
            'Lưu ý: Thông báo này có mức độ ưu tiên cao, vui lòng đọc kỹ và thực hiện đúng hạn.',
            'Chú ý: Vui lòng thực hiện theo hướng dẫn để tránh gặp sự cố về sau.',
            'Quan trọng: Không tuân thủ quy định có thể ảnh hưởng đến việc học tập của bạn.',
            'Lưu ý: Liên hệ phòng Đào tạo nếu cần hỗ trợ thêm thông tin.',
            'Thông báo khẩn: Vui lòng hoàn thành trong thời gian quy định.'
        ],
        'schedule': [
            'Lưu ý: Mang theo thẻ sinh viên và CMND/CCCD khi đến lớp.',
            'Chú ý: Đến đúng giờ để không bị coi là nghỉ học.',
            'Quan trọng: Kiểm tra phòng học trước khi đến để tránh nhầm lẫn.',
            'Lưu ý: Thông báo thay đổi lịch học sẽ được cập nhật trên Portal.',
            'Chú ý: Vắng mặt quá 3 buổi có thể bị cấm thi.'
        ],
        'tuition': [
            'Lưu ý: Đóng học phí đúng hạn để tránh bị khóa tài khoản Portal.',
            'Quan trọng: Sinh viên chưa đóng học phí sẽ không được đăng ký môn học kỳ tiếp theo.',
            'Chú ý: Lưu giữ biên lai đóng học phí để đối chiếu khi cần thiết.',
            'Lưu ý: Có thể đóng học phí qua ngân hàng hoặc trực tiếp tại trường.',
            'Thông báo: Học phí chậm nộp sẽ bị tính phí phạt 50,000đ/ngày.'
        ],
        'event': [
            'Lưu ý: Đăng ký tham gia sự kiện trước để được ưu tiên chỗ ngồi.',
            'Chú ý: Mang theo thẻ sinh viên để được xác nhận tham dự.',
            'Quan trọng: Trang phục lịch sự khi tham gia sự kiện.',
            'Lưu ý: Sự kiện có thể thay đổi thời gian, theo dõi thông báo mới nhất.',
            'Chú ý: Số lượng chỗ ngồi có hạn, đến sớm để có chỗ tốt nhất.'
        ]
    }
    
    # ============================================================
    # SPECIAL NOTIFICATIONS FOR TEST ACCOUNTS (appended on top)
    # ============================================================
    test_notification_templates = [
        ('important', 'Thông báo đặc biệt cho tài khoản test', 'Đây là thông báo dành riêng cho tài khoản test của bạn', None),
        ('schedule', 'Lịch thi cuối kỳ - Test Account', 'Vui lòng kiểm tra lịch thi trên Portal. Đây là thông báo test.', None),
        ('tuition', 'Nhắc nhở học phí - Test Account', 'Vui lòng kiểm tra tình trạng học phí trên Portal', None),
        ('event', 'Sự kiện đặc biệt - Test Account', 'Thông báo sự kiện dành riêng cho tài khoản test', 'Hội trường A'),
        ('important', 'Cập nhật thông tin tài khoản', 'Vui lòng cập nhật thông tin cá nhân trên Portal', None),
    ]
    
    # Get test student account
    test_student_account = self.data.get('fixed_accounts', {}).get('student')
    if test_student_account:
        test_student_id = test_student_account.get('student_id')
        test_student_class_id = test_student_account.get('class_id')
        
        if test_student_id and test_student_class_id:
            # Create 4x more notifications specifically for test student (80 total)
            num_student_notifs = 80
            for i in range(num_student_notifs):
                notif_type, title, content, location = random.choice(test_notification_templates)
                
                # Generate notice message based on notification type
                notice_message = random.choice(notice_messages.get(notif_type, ['']))
                
                # Schedule across 2 years past to 1 week future with varied times
                days_offset = random.randint(-731, 7)  # 2 years ago to 1 week future
                hours_offset = random.randint(0, 23)   # Random hour 0-23
                minutes_offset = random.randint(0, 59) # Random minute 0-59
                
                # Create scheduled time with varied hours and minutes
                scheduled = base_date + timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset)
                
                # Visible time: 0-2 days before scheduled, also with random time
                visible_days_before = random.randint(0, 2)
                visible_hours = random.randint(0, 23)
                visible_minutes = random.randint(0, 59)
                visible = scheduled - timedelta(days=visible_days_before, hours=visible_hours, minutes=visible_minutes)
                
                # Created time: 1-5 days before visible, also with random time
                created_days_before = random.randint(1, 5)
                created_hours = random.randint(0, 23)
                created_minutes = random.randint(0, 59)
                created = visible - timedelta(days=created_days_before, hours=created_hours, minutes=created_minutes)
                
                status = 'sent' if scheduled < base_date else 'pending'
                is_read = 0
                is_deleted = 0
                is_active = 1
                
                updated = None
                if random.random() < 0.2:
                    updated_hours = random.randint(0, 23)
                    updated_minutes = random.randint(0, 59)
                    updated = (created + timedelta(days=1, hours=updated_hours, minutes=updated_minutes)).strftime('%Y-%m-%d %H:%M:%S')
                
                event_start = None
                if notif_type == 'event':
                    event_days = random.randint(1, 14)
                    event_hours = random.randint(8, 20)  # Events usually during business hours
                    event_minutes = random.choice([0, 15, 30, 45])  # Events usually start at quarter hours
                    event_start = (scheduled + timedelta(days=event_days, hours=event_hours, minutes=event_minutes)).strftime('%Y-%m-%d %H:%M:%S')
                
                schedule_id = self.generate_uuid()
                
                # Use 'student' target_type with student_id (targets specific student directly)
                notification_rows.append([
                    schedule_id,
                    notif_type,
                    title,
                    content,
                    notice_message,
                    scheduled.strftime('%Y-%m-%d %H:%M:%S'),
                    visible.strftime('%Y-%m-%d %H:%M:%S'),
                    is_read,
                    'student',  # target_type - direct to student
                    test_student_id,  # target_id (specific student)
                    admin_id,
                    status,
                    location,
                    event_start,
                    created.strftime('%Y-%m-%d %H:%M:%S'),
                    updated,
                    is_deleted,
                    is_active
                ])
                
                # Store for notification_user_read
                if 'notifications' not in self.data:
                    self.data['notifications'] = []
                self.data['notifications'].append({
                    'schedule_id': schedule_id,
                    'visible_from': visible
                })
            
            self.add_statement(f"-- Added {num_student_notifs} special notifications (4x increase) for test student (student.test@edu.vn) with target_type='student'")
    
    # Get test instructor account
    test_instructor_account = self.data.get('fixed_accounts', {}).get('instructor')
    if test_instructor_account:
        test_instructor_id = test_instructor_account.get('instructor_id')
        
        if test_instructor_id:
            # Create 4x more notifications specifically for test instructor (80 total)
            num_instructor_notifs = 80
            for i in range(num_instructor_notifs):
                notif_type, title, content, location = random.choice(test_notification_templates)
                
                # Generate notice message based on notification type
                notice_message = random.choice(notice_messages.get(notif_type, ['']))
                
                # Schedule across 2 years past to 1 week future with varied times
                days_offset = random.randint(-731, 7)  # 2 years ago to 1 week future
                hours_offset = random.randint(0, 23)   # Random hour 0-23
                minutes_offset = random.randint(0, 59) # Random minute 0-59
                
                # Create scheduled time with varied hours and minutes
                scheduled = base_date + timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset)
                
                # Visible time: 0-2 days before scheduled, also with random time
                visible_days_before = random.randint(0, 2)
                visible_hours = random.randint(0, 23)
                visible_minutes = random.randint(0, 59)
                visible = scheduled - timedelta(days=visible_days_before, hours=visible_hours, minutes=visible_minutes)
                
                # Created time: 1-5 days before visible, also with random time
                created_days_before = random.randint(1, 5)
                created_hours = random.randint(0, 23)
                created_minutes = random.randint(0, 59)
                created = visible - timedelta(days=created_days_before, hours=created_hours, minutes=created_minutes)
                
                status = 'sent' if scheduled < base_date else 'pending'
                is_read = 0
                is_deleted = 0
                is_active = 1
                
                updated = None
                if random.random() < 0.2:
                    updated_hours = random.randint(0, 23)
                    updated_minutes = random.randint(0, 59)
                    updated = (created + timedelta(days=1, hours=updated_hours, minutes=updated_minutes)).strftime('%Y-%m-%d %H:%M:%S')
                
                event_start = None
                if notif_type == 'event':
                    event_days = random.randint(1, 14)
                    event_hours = random.randint(8, 20)  # Events usually during business hours
                    event_minutes = random.choice([0, 15, 30, 45])  # Events usually start at quarter hours
                    event_start = (scheduled + timedelta(days=event_days, hours=event_hours, minutes=event_minutes)).strftime('%Y-%m-%d %H:%M:%S')
                
                schedule_id = self.generate_uuid()
                
                # Use 'instructor' target_type with instructor_id (targets specific instructor)
                notification_rows.append([
                    schedule_id,
                    notif_type,
                    title,
                    content,
                    notice_message,
                    scheduled.strftime('%Y-%m-%d %H:%M:%S'),
                    visible.strftime('%Y-%m-%d %H:%M:%S'),
                    is_read,
                    'instructor',  # target_type
                    test_instructor_id,  # target_id (specific instructor)
                    admin_id,
                    status,
                    location,
                    event_start,
                    created.strftime('%Y-%m-%d %H:%M:%S'),
                    updated,
                    is_deleted,
                    is_active
                ])
                
                # Store for notification_user_read
                if 'notifications' not in self.data:
                    self.data['notifications'] = []
                self.data['notifications'].append({
                    'schedule_id': schedule_id,
                    'visible_from': visible
                })
            
            self.add_statement(f"-- Added {num_instructor_notifs} special notifications (4x increase) for test instructor (instructor.test@edu.vn) with target_type='instructor'")
    
    # Simple notification templates
    titles = [
        ('event', 'Hội thảo AI/ML', 'Giảng viên Google Vietnam. 14:00-17:00', 'Hội trường A'),
        ('event', 'Workshop Mobile', 'React Native và Flutter. 3 tiếng', 'Lab 1'),
        ('event', 'Cuộc thi Lập trình', 'Giải nhất 50 triệu. Đội 3-5 người', 'Lab tổng hợp'),
        ('event', 'Ngày hội việc làm', '50 doanh nghiệp tuyển dụng', 'Nhà thi đấu'),
        ('event', 'Giải bóng đá', 'Tranh cúp Hiệu trưởng. Giải 10 triệu', 'Sân vận động'),
        ('tuition', 'Đóng học phí HK1', 'Hạn cuối 30/12. Mức 8.5 triệu. TK: 0123456789', None),
        ('tuition', 'HẠN CUỐI học phí', 'Còn 5 ngày. Chưa đóng bị khóa tài khoản', None),
        ('tuition', 'Xác nhận học phí', 'Đã hoàn tất. Kiểm tra biên lai trên Portal', None),
        ('tuition', 'Hỗ trợ học phí', 'Nộp hồ sơ trước 15/12. Hỗ trợ đến 50%', None),
        ('schedule', 'Thay đổi lịch học', 'CTDL: Thứ 2 7h sang Thứ 3 9h, B202', None),
        ('schedule', 'HỦY buổi 15/12', 'CSDL hủy. Học bù 22/12 Lab 2', None),
        ('schedule', 'Lịch thi giữa kỳ', 'OOP: 20/12 13:00 phòng A101. Mang CMND', None),
        ('schedule', 'Lịch thi cuối kỳ', 'Tra cứu Portal từ 01/12. Thi 09/01-25/01', None),
        ('schedule', 'Đăng ký môn HK2', '15/12-25/12. Tối đa 24 TC. Xem Portal', None),
        ('important', 'Cập nhật thông tin', 'Cập nhật email, SĐT trước 20/12', None),
        ('important', 'Quy chế đào tạo mới', 'Điểm qua môn 5.0. Học tối đa 6 năm', None),
        ('important', 'Khảo sát giảng dạy', '10-15 phút. Trúng thưởng 500k. Hạn 25/12', None),
        ('important', 'Bảo trì Portal', '18/12 00:00-06:00. Hoàn thành đăng ký trước', None),
        ('important', 'Xét học bổng HK1', 'GPA>=3.5. Hồ sơ trước 30/12. 2-5 triệu/kỳ', None),
    ]
    
    # Available target types with weights
    target_type_options = [
        ('all', None, 0.15),                    # 15% - Everyone
        ('all_students', None, 0.30),          # 30% - All students
        ('all_instructors', None, 0.15),       # 15% - All instructors
        ('class', 'class_id', 0.20),           # 20% - Specific class
        ('faculty', 'faculty_id', 0.15),       # 15% - Specific faculty
        ('instructor', 'instructor_id', 0.05), # 5% - Specific instructor
    ]
    
    # Generate 4x more notifications (800 total) spread across past 2 years to 1 week in future
    num_notifications = 800
    
    for i in range(num_notifications):
        notif_type, title, content, location = random.choice(titles)
        
        # Generate notice message based on notification type
        notice_message = random.choice(notice_messages.get(notif_type, ['']))
        
        # Random timing spread across 2 years past to 1 week future (731 + 7 = 738 days range)
        days_offset = random.randint(-731, 7)  # 2 years ago to 1 week future
        hours_offset = random.randint(0, 23)   # Random hour 0-23
        minutes_offset = random.randint(0, 59) # Random minute 0-59
        
        # Create scheduled time with varied hours and minutes
        scheduled = base_date + timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset)
        
        # Visible time: 0-2 days before scheduled, also with random time
        visible_days_before = random.randint(0, 2)
        visible_hours = random.randint(0, 23)
        visible_minutes = random.randint(0, 59)
        visible = scheduled - timedelta(days=visible_days_before, hours=visible_hours, minutes=visible_minutes)
        
        # Created time: 1-5 days before visible, also with random time
        created_days_before = random.randint(1, 5)
        created_hours = random.randint(0, 23)
        created_minutes = random.randint(0, 59)
        created = visible - timedelta(days=created_days_before, hours=created_hours, minutes=created_minutes)
        
        # Status
        status = 'sent' if scheduled < base_date else 'pending'
        if status == 'sent' and random.random() > 0.9:
            status = 'cancelled'
        
        # Read status - set to 0 (unread) since read status is tracked per-user in notification_user_read table
        is_read = 0
        
        # Active/deleted
        is_deleted = 1 if random.random() > 0.97 else 0
        is_active = 0 if is_deleted else 1
        
        # Updated timestamp with random time
        updated = None
        if random.random() < 0.3:
            updated_days = random.randint(1, 3)
            updated_hours = random.randint(0, 23)
            updated_minutes = random.randint(0, 59)
            updated = (created + timedelta(days=updated_days, hours=updated_hours, minutes=updated_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Event fields with random time
        event_start = None
        if notif_type == 'event':
            event_days = random.randint(1, 21)
            event_hours = random.randint(8, 20)  # Events usually during business hours
            event_minutes = random.choice([0, 15, 30, 45])  # Events usually start at quarter hours
            event_start = (scheduled + timedelta(days=event_days, hours=event_hours, minutes=event_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Randomly select target type based on weights
        rand_val = random.random()
        cumulative = 0
        target_type = 'all_students'  # default
        target_id = None
        
        for target, id_field, weight in target_type_options:
            cumulative += weight
            if rand_val <= cumulative:
                target_type = target
                # Set target_id if needed
                if id_field == 'class_id' and self.data.get('classes'):
                    target_id = random.choice(self.data['classes'])['class_id']
                elif id_field == 'faculty_id' and self.data.get('faculties'):
                    target_id = random.choice(self.data['faculties'])['faculty_id']
                elif id_field == 'instructor_id' and self.data.get('instructors'):
                    target_id = random.choice(self.data['instructors'])['instructor_id']
                break
        
        schedule_id = self.generate_uuid()
        
        notification_rows.append([
            schedule_id,
            notif_type,
            title,
            content,
            notice_message,
            scheduled.strftime('%Y-%m-%d %H:%M:%S'),
            visible.strftime('%Y-%m-%d %H:%M:%S'),
            is_read,
            target_type,
            target_id,
            admin_id,
            status,
            location,
            event_start,
            created.strftime('%Y-%m-%d %H:%M:%S'),
            updated,
            is_deleted,
            is_active
        ])
        
        # Store for notification_user_read
        if 'notifications' not in self.data:
            self.data['notifications'] = []
        self.data['notifications'].append({
            'schedule_id': schedule_id,
            'visible_from': visible
        })
    
    self.add_statement(f"-- Generated {len(notification_rows)} notifications")
    
    self.bulk_insert('notification_schedule',
                    ['schedule_id', 'notification_type', 'title', 'content', 'notice_message',
                     'scheduled_date', 'visible_from', 'is_read', 'target_type',
                     'target_id', 'created_by_user', 'status', 'event_location',
                     'event_start_date', 'created_at', 'updated_at', 'is_deleted',
                     'is_active'],
                    notification_rows)

def create_notification_user_read(self):
    """Simple: Randomly mark 20% of notifications as read for test accounts"""
    self.add_statement("\n-- ==================== NOTIFICATION USER READ ====================")
    
    import random
    from datetime import datetime, timedelta
    
    if not self.data.get('notifications'):
        self.add_statement("-- WARNING: No notifications found. Run create_notifications first.")
        return
    
    # Get test account user IDs from spec
    test_student_user_id = None
    test_instructor_user_id = None
    
    # Find test accounts from fixed_accounts
    for key, account in self.data.get('fixed_accounts', {}).items():
        if key == 'student' and account.get('user_id'):
            test_student_user_id = account['user_id']
        elif key == 'instructor' and account.get('user_id'):
            test_instructor_user_id = account['user_id']
    
    if not test_student_user_id or not test_instructor_user_id:
        self.add_statement("-- WARNING: Test account user IDs not found")
        return
    
    read_rows = []
    base_date = datetime.now()
    
    # For each test account, randomly mark 20% of notifications as read
    for user_id in [test_student_user_id, test_instructor_user_id]:
        # Get 20% of notifications randomly
        num_to_read = max(1, int(len(self.data['notifications']) * 0.2))
        selected_notifications = random.sample(self.data['notifications'], num_to_read)
        
        for notif in selected_notifications:
            # Random read_at time (within last 30 days) with varied hours and minutes
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            read_at = base_date - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            read_rows.append([
                self.generate_uuid(),
                notif['schedule_id'],
                user_id,
                read_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    self.add_statement(f"-- Generated {len(read_rows)} notification_user_read entries (20% of notifications for each test account)")
    
    if read_rows:
        self.bulk_insert('notification_user_read',
                        ['notification_user_read_id', 'schedule_id', 'user_id', 'read_at'],
                        read_rows)

def create_documents(self):
    """
    Generate document records for course materials
    Associates documents with course_classes and instructors
    Now supports both file_title and file_name columns:
    - file_title: Uses the description as the display title
    - file_name: File name with extension truncated
    """
    self.add_statement("\n-- ==================== COURSE DOCUMENTS ====================")
    self.add_statement("-- Generating course material documents (PDFs, images, Excel files)")
    self.add_statement("-- UPDATED: Now supports file_title (description) and file_name (without extension)")
    self.add_statement("-- FIXED: Upload dates now properly constrained within course class dates (not semester dates)")
    self.add_statement("-- IMPROVED: Upload dates vary throughout course class duration with realistic timing:")
    self.add_statement("--   - Tài liệu, Slide: Early in course class (first 30%)")
    self.add_statement("--   - Bài LAB: Mid-late in course class (40%-90%)")
    self.add_statement("--   - Bài tập: Throughout course class (10%-90%)")
    self.add_statement("--   - Hours: Business hours (8 AM-6 PM) + some evening uploads")
    
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
    
    # Document types (matching CHECK constraint)
    document_types = ['Bài tập', 'Tài liệu', 'Slide', 'Bài LAB']
    
    # Document type descriptions mapped to document types
    descriptions = {
        'Bài tập': [
            'Bài tập thực hành tuần',
            'Bài tập ôn tập',
            'Đề bài tập lớn',
            'Bài tập làm thêm'
        ],
        'Tài liệu': [
            'Bài giảng lý thuyết',
            'Tài liệu tham khảo',
            'Đề cương môn học',
            'Tài liệu ôn tập',
            'Giáo trình môn học'
        ],
        'Slide': [
            'Slide bài giảng',
            'Slide tổng quan',
            'Slide minh họa',
            'Slide thảo luận'
        ],
        'Bài LAB': [
            'Hướng dẫn thực hành',
            'Bài LAB thực hành',
            'Đề bài thí nghiệm',
            'Mẫu báo cáo LAB'
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
        
        # FIXED: Get actual course class dates (not semester dates) for realistic document upload timing
        course_start = course_class.get('course_class_start')
        course_end = course_class.get('course_class_end')
        
        for i in range(num_docs):
            document_id = self.generate_uuid()
            
            # Randomly select document type
            document_type = random.choice(document_types)
            
            # Randomly select file type and file
            file_category = random.choice(['pdf', 'image', 'excel'])
            
            if file_category == 'pdf' and pdf_files:
                file_name = random.choice(pdf_files)
                file_type = 'pdf'
            elif file_category == 'image' and image_files:
                file_name = random.choice(image_files)
                file_ext = file_name.split('.')[-1].lower()
                file_type = file_ext if file_ext in ['jpg', 'jpeg', 'png'] else 'jpg'
            elif file_category == 'excel' and excel_files:
                file_name = random.choice(excel_files)
                file_ext = file_name.split('.')[-1].lower()
                file_type = file_ext if file_ext in ['xlsx', 'xls'] else 'xlsx'
            else:
                # Fallback to PDF if preferred type not available
                if pdf_files:
                    file_name = random.choice(pdf_files)
                    file_type = 'pdf'
                else:
                    continue
            
            # Build file path URL using correct bucket
            file_path = self.media_scanner.build_url('instructor_documents', file_name)
            
            # Generate file size
            size_min, size_max = file_size_ranges.get(file_type, (100000, 5000000))
            file_size = random.randint(size_min, size_max)
            
            # Get description based on document type
            desc_pool = descriptions[document_type]
            description = random.choice(desc_pool)
            
            # Uploaded by instructor
            uploaded_by = course_class.get('instructor_id')
            
            # Generate varied upload dates throughout the semester
            upload_date = None
            if course_start and course_end:
                # Convert string dates to datetime objects if needed
                if isinstance(course_start, str):
                    from datetime import datetime as dt
                    course_start = dt.strptime(course_start, '%Y-%m-%d').date()
                if isinstance(course_end, str):
                    from datetime import datetime as dt
                    course_end = dt.strptime(course_end, '%Y-%m-%d').date()
                
                # Generate random date within semester with varied hours/minutes
                total_days = (course_end - course_start).days
                if total_days > 0:
                    # Document type influences upload timing within course class duration:
                    # - Tài liệu, Slide: Early in course class (first 30%)
                    # - Bài tập: Throughout course class (10%-90%)
                    # - Bài LAB: Mid to late course class (40%-90%)
                    if document_type in ['Tài liệu', 'Slide']:
                        # Upload early (first 30% of course class duration)
                        random_days = random.randint(1, max(1, int(total_days * 0.3)))
                    elif document_type == 'Bài LAB':
                        # Upload mid to late (40%-90% of course class duration)
                        random_days = random.randint(int(total_days * 0.4), max(1, int(total_days * 0.9)))
                    else:  # Bài tập
                        # Upload throughout course class (10%-90%)
                        random_days = random.randint(int(total_days * 0.1), max(1, int(total_days * 0.9)))
                    
                    # Random hour during business hours (8 AM - 6 PM) with some after hours
                    hour = random.choice([8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18] + 
                                       [19, 20, 21] * 2)  # Some evening uploads
                    minute = random.choice([0, 15, 30, 45, random.randint(0, 59)])  # Mix of on-the-hour and random
                    
                    upload_date = datetime.combine(
                        course_start + timedelta(days=random_days),
                        datetime.min.time().replace(hour=hour, minute=minute)
                    )
            
            # Fallback to random date if course dates not available
            if not upload_date:
                # Random date within last year
                days_ago = random.randint(30, 365)
                hour = random.randint(8, 21)
                minute = random.randint(0, 59)
                upload_date = datetime.now() - timedelta(days=days_ago)
                upload_date = upload_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Generate file_title (use description as the title)
            file_title = description
            
            # Generate file_name by truncating extension from original filename
            file_name_without_ext = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            
            document_rows.append([
                document_id,
                course_class['course_class_id'],
                file_title,
                file_name_without_ext,
                document_type,
                file_path,
                file_type,
                file_size,
                uploaded_by,
                description,
                upload_date.strftime('%Y-%m-%d %H:%M:%S')  # Add created_at timestamp
            ])
    
    self.add_statement(f"-- Total documents generated: {len(document_rows)}")
    
    self.bulk_insert('document',
                    ['document_id', 'course_class_id', 'file_title', 'file_name', 'document_type',
                     'file_path', 'file_type', 'file_size', 'uploaded_by', 'description', 'created_at'],
                    document_rows)

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

def create_notes(self):
    """Generate simple one-line notes for the test student"""
    self.add_statement("\n-- ==================== STUDENT NOTES ====================")
    
    import random
    from datetime import datetime, timedelta
    
    # FIXED TEST STUDENT ID
    test_student_id = '00000000-0000-0000-0000-000000000003'
    
    note_rows = []
    
    # Simple one-line note content
    note_contents = [
        'Nhắc nhở: Thi giữa kỳ vào tuần sau',
        'Còn 5 ngày nữa đến kỳ thi cuối kỳ',
        'Thi tuần này - Phòng A101, đến trước 15 phút',
        'Kỳ thi thực hành trên máy - Cần chuẩn bị tài khoản đăng nhập',
        'Ôn tập chương 3: Cấu trúc dữ liệu (Stack, Queue, Linked List, Tree)',
        'Cần xem lại: Bài giảng tuần 5-6 về thuật toán sắp xếp',
        'Làm lại bài tập về con trỏ - Bài 4.3, 4.7, 4.9',
        'Ôn thi: Tập trung Database Normalization (1NF, 2NF, 3NF, BCNF)',
        'Học nhóm: Ôn chương 2 với bạn vào thứ 5',
        'Bài tập tuần 7 - Deadline 3 ngày nữa (Stack, Queue, BST)',
        'Hoàn thành Lab 4 trước buổi học - Chương trình quản lý sinh viên',
        'Bài tập nhóm - Thuyết trình tuần sau (Hoàn thiện slide và demo)',
        'Đọc tài liệu chương 5 trước lớp (Section 5.1-5.3)',
        'Tổng hợp: Lập trình hướng đối tượng (Class, Inheritance, Polymorphism)',
        'Công thức quan trọng cần nhớ: Tổ hợp C(n,k), Hoán vị P(n,k)',
        'Tổng hợp bài tập đã chữa trên lớp (Tuần 1-3)',
        'Lý thuyết trọng tâm: SQL Queries (SELECT, JOIN, GROUP BY)',
        'Ghi chú buổi học 15/11: Graph, BFS và DFS algorithms',
        'Lưu ý từ giảng viên về đồ án: Deadline 20/12, nhóm 3-4 người',
        'Slide bài giảng đã được đăng - Chương 4 và 5',
        'Meeting với nhóm - Thứ 5 lúc 14:00 để review tiến độ project',
        'Kế hoạch ôn thi cuối kỳ: 3 tuần ôn tập từng chương',
        'Lịch học tuần này: T2 Toán, T3 Lập trình, T5 CSDL',
        'Mục tiêu học tập tháng này: GPA >= 3.5 và hoàn thành đồ án',
        'Chuẩn bị giấy nháp cho bài thi viết tay',
        'Không được sử dụng điện thoại trong phòng thi',
        'Sinh viên cần mang theo CMND/CCCD và thẻ sinh viên',
        'Bài thi có thời gian 120 phút, không được mang tài liệu',
        'Ôn lại các khái niệm khó từ chương 1 đến chương 4',
        'Làm đề thi mẫu để làm quen với format câu hỏi',
    ]
    
    # Generate 10-15 random notes for test student
    total_notes_to_generate = random.randint(10, 15)
    
    for i in range(total_notes_to_generate):
        note_id = self.generate_uuid()
        
        # Randomly select note content
        content = random.choice(note_contents)
        
        # Random date within last 30 days or future 30 days
        days_offset = random.randint(-60, 1)
        created_at = datetime.now() + timedelta(days=days_offset)
        
        # 20% have updated_at (edited notes)
        updated_at = None
        if random.random() < 0.2:
            updated_at = (created_at + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d %H:%M:%S')
        
        note_rows.append([
            note_id,
            test_student_id,
            content,
            created_at.strftime('%Y-%m-%d %H:%M:%S'),
            updated_at
        ])
    
    self.add_statement(f"-- Generated {len(note_rows)} notes for test student")
    
    self.bulk_insert('note',
                    ['note_id', 'student_id', 'content', 'created_at', 'updated_at'],
                    note_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_notes = create_notes

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_schedule_changes = create_schedule_changes
SQLDataGenerator.create_notifications = create_notifications
SQLDataGenerator.create_notification_user_read = create_notification_user_read
SQLDataGenerator.create_documents = create_documents
SQLDataGenerator.create_regulations = create_regulations
SQLDataGenerator.create_notes = create_notes