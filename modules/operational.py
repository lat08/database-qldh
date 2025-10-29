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
    target_types = ['all', 'all_students', 'all_instructors']
    
    # Create 20 sample notifications
    for i in range(20):
        schedule_id = self.generate_uuid()
        notif_type = random.choice(notification_types)
        target_type = random.choice(target_types)
        
        scheduled_date = datetime.now() - timedelta(days=random.randint(0, 90))
        visible_from = scheduled_date - timedelta(days=random.randint(1, 7))
        
        titles = {
            'event': f'Sự kiện: Hội thảo khoa học #{i+1}',
            'tuition': f'Thông báo: Đóng học phí kỳ {i+1}',
            'schedule': f'Thay đổi lịch học tuần {i+1}',
            'important': f'Thông báo quan trọng #{i+1}'
        }
        
        notification_rows.append([
            schedule_id,
            notif_type,
            titles.get(notif_type, 'Thông báo'),
            f'Nội dung thông báo số {i+1}',
            scheduled_date,
            visible_from,
            0,  # is_read
            target_type,
            None,  # target_id
            admin_user_id,
            'sent'
        ])
    
    self.add_statement(f"-- Total notifications: {len(notification_rows)}")
    
    self.bulk_insert('notification_schedule',
                    ['schedule_id', 'notification_type', 'title', 'content',
                    'scheduled_date', 'visible_from', 'is_read', 'target_type',
                    'target_id', 'created_by_user', 'status'],
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
    
    # Document type descriptions
    descriptions = {
        'pdf': [
            'Bài giảng lý thuyết',
            'Tài liệu tham khảo',
            'Đề cương môn học',
            'Slide bài giảng',
            'Tài liệu ôn tập'
        ],
        'image': [
            'Hình ảnh minh họa',
            'Sơ đồ tư duy',
            'Biểu đồ phân tích',
            'Ảnh thực hành'
        ],
        'excel': [
            'Bảng dữ liệu mẫu',
            'Điểm danh sinh viên',
            'Kết quả thực hành',
            'Bảng tính thống kê'
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
            
            # Randomly select document type and file
            doc_type = random.choice(['pdf', 'image', 'excel'])
            
            if doc_type == 'pdf' and pdf_files:
                file_name = random.choice(pdf_files)
                file_type = 'pdf'
                desc_pool = descriptions['pdf']
            elif doc_type == 'image' and image_files:
                file_name = random.choice(image_files)
                file_ext = file_name.split('.')[-1].lower()
                file_type = file_ext if file_ext in ['jpg', 'jpeg', 'png'] else 'jpg'
                desc_pool = descriptions['image']
            elif doc_type == 'excel' and excel_files:
                file_name = random.choice(excel_files)
                file_ext = file_name.split('.')[-1].lower()
                file_type = file_ext if file_ext in ['xlsx', 'xls'] else 'xlsx'
                desc_pool = descriptions['excel']
            else:
                # Fallback to PDF if preferred type not available
                if pdf_files:
                    file_name = random.choice(pdf_files)
                    file_type = 'pdf'
                    desc_pool = descriptions['pdf']
                else:
                    continue
            
            # Build file path URL using correct bucket
            file_path = self.media_scanner.build_url('instructor_documents', file_name)
            
            # Generate file size
            size_min, size_max = file_size_ranges.get(file_type, (100000, 5000000))
            file_size = random.randint(size_min, size_max)
            
            # Random description
            description = random.choice(desc_pool)
            
            # Uploaded by instructor
            uploaded_by = course_class.get('instructor_id')
            
            document_rows.append([
                document_id,
                course_class['course_class_id'],
                file_name,
                file_path,
                file_type,
                file_size,
                uploaded_by,
                description
            ])
    
    self.add_statement(f"-- Total documents generated: {len(document_rows)}")
    
    self.bulk_insert('document',
                    ['document_id', 'course_class_id', 'file_name', 'file_path',
                    'file_type', 'file_size', 'uploaded_by', 'description'],
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


from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_schedule_changes = create_schedule_changes
SQLDataGenerator.create_notifications = create_notifications
SQLDataGenerator.create_documents = create_documents
SQLDataGenerator.create_regulations = create_regulations