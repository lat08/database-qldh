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
    """
    NEW: Generate notification schedules
    """
    self.add_statement("\n-- ==================== NOTIFICATIONS ====================")
    
    notification_rows = []
    
    # Get admin user for creating notifications
    admin_user_id = self.data['fixed_accounts']['admin']['user_id']
    
    notification_types = ['event', 'tuition', 'schedule', 'important']
    target_types = ['all', 'all_students', 'all_instructors', 'class', 'faculty', 'instructor']
    statuses = ['pending', 'sent', 'cancelled']
    
    # Create 20 sample notifications
    for i in range(50):
        schedule_id = self.generate_uuid()
        notif_type = random.choice(notification_types)
        target_type = random.choice(target_types)
        status = random.choice(statuses)
        
        # target_id will be None for now - you can populate it later if needed
        target_id = None
        
        scheduled_date = datetime.now() - timedelta(days=random.randint(0, 90))
        visible_from = scheduled_date - timedelta(days=random.randint(1, 7))
        created_at = visible_from - timedelta(days=random.randint(1, 5))
        updated_at = created_at + timedelta(days=random.randint(0, 3)) if random.random() > 0.5 else None
        
        # Event-specific fields
        event_location = None
        event_start_date = None
        if notif_type == 'event':
            event_location = random.choice(['Hội trường A', 'Phòng 101', 'Sân trường', 'Phòng hội thảo B', 'Khu vực ngoài trời'])
            event_start_date = scheduled_date + timedelta(days=random.randint(1, 14))
        
        titles = {
            'event': f'Sự kiện: Hội thảo khoa học #{i+1}',
            'tuition': f'Thông báo: Đóng học phí kỳ {i+1}',
            'schedule': f'Thay đổi lịch học tuần {i+1}',
            'important': f'Thông báo quan trọng #{i+1}'
        }
        
        is_read = 1 if random.random() > 0.7 else 0
        is_deleted = 1 if random.random() > 0.95 else 0
        is_active = 0 if is_deleted else (0 if random.random() > 0.9 else 1)
        
        notification_rows.append([
            schedule_id,
            notif_type,
            titles.get(notif_type, 'Thông báo'),
            f'Nội dung thông báo số {i+1}. Đây là thông tin chi tiết về {titles.get(notif_type, "thông báo")}.',
            scheduled_date,
            visible_from,
            is_read,
            target_type,
            target_id,
            admin_user_id,
            status,
            event_location,
            event_start_date,
            created_at,
            updated_at,
            is_deleted,
            is_active
        ])
    
    self.add_statement(f"-- Total notifications: {len(notification_rows)}")
    
    self.bulk_insert('notification_schedule',
                    ['schedule_id', 'notification_type', 'title', 'content',
                    'scheduled_date', 'visible_from', 'is_read', 'target_type',
                    'target_id', 'created_by_user', 'status', 'event_location',
                    'event_start_date', 'created_at', 'updated_at', 'is_deleted',
                    'is_active'],
                    notification_rows)

def create_documents(self):
    """
    Generate document records for course materials
    Associates documents with course_classes and instructors
    """
    self.add_statement("\n-- ==================== COURSE DOCUMENTS ====================")
    self.add_statement("-- Generating course material documents (PDFs, images, Excel files)")
    
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
            
            document_rows.append([
                document_id,
                course_class['course_class_id'],
                file_name,
                document_type,
                file_path,
                file_type,
                file_size,
                uploaded_by,
                description
            ])
    
    self.add_statement(f"-- Total documents generated: {len(document_rows)}")
    
    self.bulk_insert('document',
                    ['document_id', 'course_class_id', 'file_name', 'document_type',
                     'file_path', 'file_type', 'file_size', 'uploaded_by', 'description'],
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
    """Generate course-focused notes for the test student"""
    self.add_statement("\n-- ==================== STUDENT COURSE NOTES ====================")
    
    import random
    from datetime import datetime, timedelta
    
    # FIXED TEST STUDENT ID
    test_student_id = '00000000-0000-0000-0000-000000000003'
    
    note_rows = []
    
    # Course-focused note content templates
    note_contents = {
        'exam_reminder': [
            ('Nhắc nhở: Thi giữa kỳ vào tuần sau', 'Cần ôn tập chương 1-3\n• Xem lại bài tập đã làm\n• Làm đề thi mẫu', 'low'),
            ('Còn 5 ngày nữa đến kỳ thi cuối kỳ', 'Chuẩn bị:\n• Ôn tập toàn bộ kiến thức\n• Xem lại các bài tập khó\n• Chuẩn bị dụng cụ thi', 'high'),
            ('Thi tuần này - Phòng A101', 'Lưu ý:\n• Mang theo CMND/CCCD và thẻ SV\n• Đến trước 15 phút\n• Không mang tài liệu', 'low'),
            ('Kỳ thi thực hành trên máy', 'Yêu cầu:\n• Biết sử dụng công cụ X\n• Ôn lại các bài lab đã làm\n• Chuẩn bị tài khoản đăng nhập', 'high'),
        ],
        'exam_preparation': [
            ('Ôn tập chương 3: Cấu trúc dữ liệu', 'Nội dung:\n• Stack và Queue\n• Linked List\n• Tree và Graph\n• Làm bài tập 3.1-3.5', 'medium'),
            ('Cần xem lại: Bài giảng tuần 5-6', 'Trọng tâm:\n• Thuật toán sắp xếp\n• Độ phức tạp thuật toán\n• Bài tập áp dụng', 'medium'),
            ('Làm lại bài tập về con trỏ', 'Phần cần ôn:\n• Khai báo và sử dụng con trỏ\n• Cấp phát động\n• Con trỏ hàm\n• Bài tập 4.3, 4.7, 4.9', 'high'),
            ('Ôn thi: Tập trung Database Normalization', 'Kiến thức:\n• 1NF, 2NF, 3NF, BCNF\n• Functional Dependencies\n• Bài tập phân tích và chuẩn hóa', 'high'),
            ('Học nhóm: Ôn chương 2 với bạn', 'Kế hoạch:\n• Thảo luận các khái niệm khó\n• Làm bài tập nhóm\n• Giải đáp thắc mắc lẫn nhau', 'low'),
        ],
        'homework': [
            ('Bài tập tuần 7 - Deadline 3 ngày nữa', 'Nội dung:\n• Bài 1: Cài đặt Stack\n• Bài 2: Ứng dụng Queue\n• Bài 3: Binary Search Tree\n• Nộp file code + báo cáo', 'high'),
            ('Hoàn thành Lab 4 trước buổi học', 'Yêu cầu:\n• Viết chương trình quản lý sinh viên\n• Sử dụng file để lưu trữ\n• Test đầy đủ các chức năng', 'high'),
            ('Bài tập nhóm - Thuyết trình tuần sau', 'Công việc:\n• Hoàn thiện slide (Tuấn)\n• Chuẩn bị demo (Tôi)\n• Viết báo cáo (Lan)', 'medium'),
            ('Đọc tài liệu chương 5 trước lớp', 'Nội dung cần đọc:\n• Section 5.1-5.3\n• Xem video hướng dẫn\n• Ghi chú các điểm chưa hiểu', 'medium'),
        ],
        'review_topic': [
            ('Tổng hợp: Lập trình hướng đối tượng', 'Kiến thức chính:\n• Class và Object\n• Inheritance\n• Polymorphism\n• Encapsulation\n• Abstraction', 'medium'),
            ('Công thức quan trọng cần nhớ', 'Toán học:\n• Tổ hợp C(n,k)\n• Hoán vị P(n,k)\n• Độ phức tạp O(n), O(logn), O(n²)', 'high'),
            ('Tổng hợp bài tập đã chữa trên lớp', 'Danh sách:\n• Bài tập 1.1, 1.5 (Tuần 1)\n• Bài tập 2.3, 2.7 (Tuần 2)\n• Bài tập 3.2, 3.9 (Tuần 3)', 'medium'),
            ('Lý thuyết trọng tâm: SQL Queries', 'Nội dung:\n• SELECT, WHERE, JOIN\n• GROUP BY, HAVING\n• Subqueries\n• Set Operations', 'high'),
        ],
        'class_note': [
            ('Ghi chú buổi học 15/11', 'Nội dung đã học:\n• Giới thiệu về Graph\n• BFS và DFS algorithms\n• Bài tập áp dụng\n\nBài tập về nhà: Bài 6.1-6.3', 'low'),
            ('Lưu ý từ giảng viên về đồ án', 'Thông tin:\n• Deadline: 20/12\n• Làm theo nhóm 3-4 người\n• Yêu cầu demo và báo cáo\n• Chiếm 30% điểm môn học', 'high'),
            ('Slide bài giảng đã được đăng', 'Tài liệu:\n• Chương 4: Data Structures\n• Chương 5: Algorithms\n• Bài tập bổ sung\n• Code examples', 'medium'),
            ('Meeting với nhóm - Thứ 5 lúc 14:00', 'Nội dung họp:\n• Review tiến độ project\n• Phân công công việc tuần tới\n• Thảo luận vấn đề kỹ thuật', 'medium'),
        ],
        'study_plan': [
            ('Kế hoạch ôn thi cuối kỳ', 'Tuần 1:\n• Ôn chương 1-2\n• Làm 20 bài tập\n\nTuần 2:\n• Ôn chương 3-4\n• Làm đề thi mẫu\n\nTuần 3:\n• Ôn toàn bộ\n• Thi thử', 'medium'),
            ('Lịch học tuần này', 'Thứ 2: 7:00-9:00 Toán\nThứ 3: 13:00-15:00 Lập trình\nThứ 5: 9:00-11:00 Cơ sở dữ liệu\nThứ 6: Lab thực hành', 'low'),
            ('Mục tiêu học tập tháng này', 'Mục tiêu:\n• Hoàn thành 80% bài tập\n• Điểm GPA >= 3.5\n• Tham gia đủ buổi học\n• Hoàn thành đồ án đúng hạn', 'medium'),
        ],
    }
    
    # FIXED: Get enrolled course_class_ids for test student
    enrolled_course_class_ids = []
    
    # Look through enrollments to find test student's course classes
    if 'enrollments' in self.data:
        for enrollment in self.data['enrollments']:
            if enrollment['student_id'] == test_student_id:
                enrolled_course_class_ids.append(enrollment['course_class_id'])
    
    if not enrolled_course_class_ids:
        self.add_statement("-- ERROR: No course class enrollments found for test student")
        self.add_statement("-- Skipping note generation")
        return
    
    self.add_statement(f"-- Found {len(enrolled_course_class_ids)} enrolled course classes for test student")
    
    # Generate exactly 10 notes distributed across enrolled courses
    total_notes_to_generate = 10
    
    for i in range(total_notes_to_generate):
        note_id = self.generate_uuid()
        
        # Randomly select a course class from enrolled courses
        course_class_id = random.choice(enrolled_course_class_ids)
        
        # Randomly select note type and content
        note_type = random.choice(list(note_contents.keys()))
        title, content, default_priority = random.choice(note_contents[note_type])
        
        # Random date within last 30 days or future 30 days
        days_offset = random.randint(-30, 30)
        created_at = datetime.now() + timedelta(days=days_offset)
        
        # Note status - 30% completed, 70% to_do
        note_status = 'completed' if random.random() < 0.3 else 'to_do'
        
        # Priority - 70% use default, 30% random
        priority = default_priority if random.random() > 0.3 else random.choice(['low', 'medium', 'high'])
        
        note_rows.append([
            note_id,
            test_student_id,
            course_class_id,
            title,
            content,
            note_type,
            priority,
            note_status,
            created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Statistics by note type
    note_type_counts = {}
    for row in note_rows:
        note_type = row[5]
        note_type_counts[note_type] = note_type_counts.get(note_type, 0) + 1
    
    completed_count = sum(1 for row in note_rows if row[7] == 'completed')
    
    self.add_statement(f"-- Generated {len(note_rows)} notes for test student")
    self.add_statement(f"-- Distribution: {dict(note_type_counts)}")
    self.add_statement(f"-- Status: {completed_count} completed, {len(note_rows) - completed_count} to_do")
    
    self.bulk_insert('note',
                    ['note_id', 'student_id', 'course_class_id', 
                     'title', 'content', 'note_type', 'priority', 'note_status', 'created_at'],
                    note_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_schedule_changes = create_schedule_changes
SQLDataGenerator.create_notifications = create_notifications
SQLDataGenerator.create_documents = create_documents
SQLDataGenerator.create_regulations = create_regulations
SQLDataGenerator.create_notes = create_notes