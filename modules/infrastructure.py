import random
from datetime import date
from .config import *



def create_buildings_and_rooms(self):
    self.add_statement("\n-- ==================== BUILDINGS & ROOMS ====================")
    
    building_rows = []
    room_rows = []
    
    # Valid room types from schema
    room_types = [
        'exam',
        'lecture_hall',
        'classroom',
        'computer_lab',
        'laboratory',
        'meeting_room',
        'gym_room',
        'swimming_pool',
        'music_room',
        'art_room',
        'library_room',
        'self_study_room',
        'dorm_room'
    ]
    
    # Room type distribution (weighted for realistic campus)
    room_type_weights = {
        'classroom': 0.35,
        'lecture_hall': 0.15,
        'computer_lab': 0.15,
        'laboratory': 0.10,
        'exam': 0.10,
        'meeting_room': 0.05,
        'self_study_room': 0.05,
        'library_room': 0.03,
        'gym_room': 0.01,
        'music_room': 0.003,
        'art_room': 0.003,
        'swimming_pool': 0.001,
        'dorm_room': 0.003
    }
    
    # Capacity ranges by room type
    capacity_by_type = {
        'exam': (50, 100),
        'lecture_hall': (100, 300),
        'classroom': (30, 60),
        'computer_lab': (30, 50),
        'laboratory': (20, 40),
        'meeting_room': (10, 30),
        'gym_room': (50, 100),
        'swimming_pool': (30, 50),
        'music_room': (15, 30),
        'art_room': (20, 40),
        'library_room': (50, 150),
        'self_study_room': (20, 50),
        'dorm_room': (2, 4)
    }
    
    for line in self.spec_data.get('buildings', []):
        parts = [p.strip() for p in line.split('|')]
        bldg_name, bldg_code, rooms_count = parts[0], parts[1], int(parts[2])
        
        building_id = self.generate_uuid()
        self.data['buildings'].append({'building_id': building_id, 'building_name': bldg_name})
        building_rows.append([building_id, bldg_name, bldg_code, 'TP Hồ Chí Minh', 'active'])
        
        bldg_letter = bldg_code[-1]
        
        # Distribute room types across this building
        for j in range(rooms_count):
            room_id = self.generate_uuid()
            room_code = f"{bldg_letter}{j+1:02d}"
            
            # Select room type based on weights
            rand = random.random()
            cumulative = 0
            selected_type = 'classroom'  # default
            
            for rtype, weight in room_type_weights.items():
                cumulative += weight
                if rand <= cumulative:
                    selected_type = rtype
                    break
            
            # Get capacity range for this room type
            cap_min, cap_max = capacity_by_type.get(selected_type, (30, 60))
            capacity = random.randint(cap_min, cap_max)
            
            # Generate room name based on type
            room_name_map = {
                'exam': 'Phòng thi',
                'lecture_hall': 'Giảng đường',
                'classroom': 'Phòng học',
                'computer_lab': 'Phòng máy tính',
                'laboratory': 'Phòng thí nghiệm',
                'meeting_room': 'Phòng họp',
                'gym_room': 'Phòng thể dục',
                'swimming_pool': 'Hồ bơi',
                'music_room': 'Phòng âm nhạc',
                'art_room': 'Phòng mỹ thuật',
                'library_room': 'Phòng thư viện',
                'self_study_room': 'Phòng tự học',
                'dorm_room': 'Ký túc xá'
            }
            
            room_name = f"{room_name_map.get(selected_type, 'Phòng')} {room_code}"
            
            # Get random room picture
            room_pic = self.media_scanner.get_random_file('room_pics')
            room_pic_url = self.media_scanner.build_url('room_pics', room_pic) if room_pic else None
            
            # FIXED: Changed 'picture_url' to 'room_picture_path'
            self.data['rooms'].append({
                'room_id': room_id, 
                'room_code': room_code, 
                'room_name': room_name,
                'capacity': capacity,
                'room_type': selected_type,
                'room_picture_path': room_pic_url
            })
            
            room_rows.append([
                room_id, 
                room_code, 
                room_name, 
                capacity, 
                selected_type,
                building_id, 
                'active',
                room_pic_url
            ])
    
    self.add_statement(f"-- Total buildings: {len(building_rows)}")
    self.add_statement(f"-- Total rooms: {len(room_rows)}")
    
    # Room type distribution summary
    type_counts = {}
    for room in self.data['rooms']:
        rtype = room['room_type']
        type_counts[rtype] = type_counts.get(rtype, 0) + 1
    
    self.add_statement("-- Room type distribution:")
    for rtype, count in sorted(type_counts.items()):
        self.add_statement(f"--   {rtype}: {count}")
    
    self.bulk_insert('building', 
                    ['building_id', 'building_name', 'building_code', 'address', 'building_status'], 
                    building_rows)
    
    self.bulk_insert('room', 
                    ['room_id', 'room_code', 'room_name', 'capacity', 'room_type', 'building_id', 'room_status', 'room_picture_path'], 
                    room_rows)

def create_room_amenities(self):
    """
    Create room amenities (facilities/equipment available in rooms)
    """
    self.add_statement("\n-- ==================== ROOM AMENITIES ====================")
    
    amenity_rows = []
    
    # Define standard amenities
    amenities = [
        # Basic equipment
        'Máy chiếu',
        'Bảng trắng',
        'Bảng đen',
        'Màn hình chiếu',
        'Loa âm thanh',
        'Micro',
        
        # Technology
        'Máy tính giảng viên',
        'Kết nối Internet',
        'WiFi',
        'Hệ thống âm thanh',
        'Camera giám sát',
        'Màn hình tương tác',
        
        # Comfort
        'Điều hòa không khí',
        'Quạt trần',
        'Cửa sổ lớn',
        'Rèm che',
        'Ghế có đệm',
        'Bàn học điều chỉnh',
        
        # Specialized equipment
        'Thiết bị thí nghiệm',
        'Tủ hóa chất',
        'Máy tính cá nhân',
        'Bàn vẽ',
        'Nhạc cụ',
        'Thiết bị thể dục',
        'Tủ đồ cá nhân',
        'Giường nằm',
        'Tủ quần áo',
        'Kệ sách',
        'Đèn đọc sách'
    ]
    
    for amenity_name in amenities:
        amenity_id = self.generate_uuid()
        
        self.data['amenities'].append({
            'amenity_id': amenity_id,
            'amenity_name': amenity_name
        })
        
        amenity_rows.append([amenity_id, amenity_name])
    
    self.add_statement(f"-- Total amenities: {len(amenity_rows)}")
    
    self.bulk_insert('room_amenity',
                    ['amenity_id', 'amenity_name'],
                    amenity_rows)

def create_room_amenity_mappings(self):
    """
    Map amenities to rooms based on room type
    """
    self.add_statement("\n-- ==================== ROOM AMENITY MAPPINGS ====================")
    
    mapping_rows = []
    
    # Get amenity lookup by name
    amenity_lookup = {}
    for amenity in self.data['amenities']:
        # Extract English part from name for easier matching
        name = amenity['amenity_name']
        if '(' in name:
            key = name.split('(')[0].strip()
        else:
            key = name
        amenity_lookup[key] = amenity['amenity_id']
    
    # Define amenities by room type
    amenities_by_type = {
        'exam': [
            'Máy chiếu',
            'Điều hòa không khí',
            'Camera giám sát',
            'Bàn học điều chỉnh',
            'Ghế có đệm'
        ],
        'lecture_hall': [
            'Máy chiếu',
            'Màn hình chiếu',
            'Loa âm thanh',
            'Micro',
            'Bảng trắng',
            'Điều hòa không khí',
            'Máy tính giảng viên',
            'Hệ thống âm thanh',
            'WiFi',
            'Kết nối Internet'
        ],
        'classroom': [
            'Máy chiếu',
            'Bảng trắng',
            'Điều hòa không khí',
            'WiFi',
            'Kết nối Internet',
            'Cửa sổ lớn',
            'Rèm che'
        ],
        'computer_lab': [
            'Máy tính cá nhân',
            'Máy chiếu',
            'Điều hòa không khí',
            'Bảng trắng',
            'WiFi',
            'Kết nối Internet',
            'Máy tính giảng viên'
        ],
        'laboratory': [
            'Thiết bị thí nghiệm',
            'Tủ hóa chất',
            'Bảng trắng',
            'Điều hòa không khí',
            'Cửa sổ lớn',
            'WiFi',
            'Kết nối Internet'
        ],
        'meeting_room': [
            'Máy chiếu',
            'Màn hình tương tác',
            'Bảng trắng',
            'Điều hòa không khí',
            'Hệ thống âm thanh',
            'Micro',
            'WiFi',
            'Kết nối Internet',
            'Ghế có đệm'
        ],
        'gym_room': [
            'Thiết bị thể dục',
            'Tủ đồ cá nhân',
            'Quạt trần',
            'Cửa sổ lớn'
        ],
        'swimming_pool': [
            'Tủ đồ cá nhân',
            'Camera giám sát'
        ],
        'music_room': [
            'Nhạc cụ',
            'Hệ thống âm thanh',
            'Loa âm thanh',
            'Điều hòa không khí',
            'Cửa sổ lớn',
            'Tủ đồ cá nhân'
        ],
        'art_room': [
            'Bàn vẽ',
            'Cửa sổ lớn',
            'Rèm che',
            'Tủ đồ cá nhân',
            'Điều hòa không khí'
        ],
        'library_room': [
            'Kệ sách',
            'Đèn đọc sách',
            'Điều hòa không khí',
            'WiFi',
            'Kết nối Internet',
            'Máy tính cá nhân',
            'Cửa sổ lớn'
        ],
        'self_study_room': [
            'Bàn học điều chỉnh',
            'Ghế có đệm',
            'Đèn đọc sách',
            'Điều hòa không khí',
            'WiFi',
            'Kết nối Internet',
            'Cửa sổ lớn',
            'Rèm che'
        ],
        'dorm_room': [
            'Giường nằm',
            'Tủ quần áo',
            'Bàn học điều chỉnh',
            'Ghế có đệm',
            'Điều hòa không khí',
            'Cửa sổ lớn',
            'WiFi',
            'Kết nối Internet'
        ]
    }
    
    # Map amenities to rooms
    for room in self.data['rooms']:
        room_type = room['room_type']
        amenity_names = amenities_by_type.get(room_type, [])
        
        for amenity_name in amenity_names:
            amenity_id = amenity_lookup.get(amenity_name)
            
            if amenity_id:
                mapping_id = self.generate_uuid()
                
                mapping_rows.append([
                    mapping_id,
                    room['room_id'],
                    amenity_id
                ])
    
    self.add_statement(f"-- Total room-amenity mappings: {len(mapping_rows)}")
    
    # Statistics
    mappings_per_room_type = {}
    for room in self.data['rooms']:
        rtype = room['room_type']
        room_mappings = [m for m in mapping_rows if m[1] == room['room_id']]
        if rtype not in mappings_per_room_type:
            mappings_per_room_type[rtype] = []
        mappings_per_room_type[rtype].append(len(room_mappings))
    
    self.add_statement("-- Average amenities per room type:")
    for rtype, counts in sorted(mappings_per_room_type.items()):
        avg = sum(counts) / len(counts) if counts else 0
        self.add_statement(f"--   {rtype}: {avg:.1f} amenities")
    
    self.bulk_insert('room_amenity_mapping',
                    ['room_amenity_mapping_id', 'room_id', 'amenity_id'],
                    mapping_rows)

def create_room_bookings(self):
    """
    Optional function to populate room_booking table for non-exam bookings
    (meetings, events, etc.) if needed
    """
    self.add_statement("\n-- ==================== ROOM BOOKINGS (OPTIONAL) ====================")
    self.add_statement("-- Creating sample room bookings for meetings and events")
    
    booking_rows = []
    
    # Get admin user for booking
    admin_user_id = self.data['fixed_accounts']['admin']['user_id']
    
    # Generate some random room bookings for demonstration
    booking_types = ['event', 'meeting', 'other']
    num_bookings = 20  # Create 20 sample bookings
    
    for i in range(num_bookings):
        booking_id = self.generate_uuid()
        room = random.choice(self.data['rooms'])
        booking_type = random.choice(booking_types)
        
        # Random date in 2025
        booking_date = date(2025, random.randint(1, 12), random.randint(1, 28))
        start_time = f"{random.randint(8, 16):02d}:00:00"
        end_time = f"{random.randint(10, 18):02d}:00:00"
        
        purpose = f"Sample {booking_type} booking #{i+1}"
        
        booking_rows.append([
            booking_id,
            room['room_id'],
            booking_type,
            booking_date,
            start_time,
            end_time,
            admin_user_id,
            purpose,
            'confirmed'  # booking_status
        ])
    
    self.add_statement(f"-- Total room bookings: {len(booking_rows)}")
    
    self.bulk_insert('room_booking',
                    ['booking_id', 'room_id', 'booking_type', 'booking_date', 'start_time', 'end_time',
                    'booked_by', 'purpose', 'booking_status'],
                    booking_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_buildings_and_rooms = create_buildings_and_rooms
SQLDataGenerator.create_room_amenities = create_room_amenities
SQLDataGenerator.create_room_amenity_mappings = create_room_amenity_mappings
SQLDataGenerator.create_room_bookings = create_room_bookings