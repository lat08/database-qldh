USE EduManagement;
GO

-- ============================================================
-- ROLE (Vai trò người dùng)
-- ============================================================
CREATE TABLE role (
    role_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    role_name NVARCHAR(50) NOT NULL UNIQUE,
    description NVARCHAR(500),
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

-- ============================================================
-- PERMISSION (Quyền hạn)
-- ============================================================
CREATE TABLE permission (
    permission_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    permission_name NVARCHAR(100) NOT NULL UNIQUE,
    permission_description NVARCHAR(500),
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

-- ============================================================
-- ROLE_PERMISSION (Phân quyền cho vai trò)
-- ============================================================
CREATE TABLE role_permission (
    role_permission_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    role_id UNIQUEIDENTIFIER NOT NULL,
    permission_id UNIQUEIDENTIFIER NOT NULL,
    is_active BIT NOT NULL DEFAULT 1,
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    
    CONSTRAINT FK_role_permission_role FOREIGN KEY (role_id)
        REFERENCES role(role_id) ON DELETE CASCADE,
    CONSTRAINT FK_role_permission_permission FOREIGN KEY (permission_id)
        REFERENCES permission(permission_id) ON DELETE CASCADE,
    CONSTRAINT UQ_role_permission UNIQUE (role_id, permission_id)
);

-- ============================================================
-- PERSON (Thông tin cá nhân)
-- ============================================================
CREATE TABLE person (
    person_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    full_name NVARCHAR(200) NOT NULL,
    date_of_birth DATE,
    gender NVARCHAR(10) CHECK (gender IN ('male', 'female')),
    email NVARCHAR(255) NOT NULL UNIQUE,
    phone_number NVARCHAR(20),
    citizen_id NVARCHAR(50),
    address NVARCHAR(500),
    profile_picture NVARCHAR(500),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

-- ============================================================
-- USER ACCOUNT (Modified - uses role_id)
-- ============================================================
CREATE TABLE user_account (
    user_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    person_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    username NVARCHAR(100) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    password_salt NVARCHAR(255) NOT NULL,
    role_id UNIQUEIDENTIFIER NOT NULL,
    role_name NVARCHAR(50) CHECK (role_name IN ('student', 'instructor', 'admin')), -- Legacy/Backward Compatible
    email_verified BIT DEFAULT 0,
    email_verification_code NVARCHAR(255),
    account_status NVARCHAR(20) NOT NULL DEFAULT 'active' CHECK (account_status IN ('active', 'inactive', 'suspended')),
    last_login_time DATETIME2,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_user_account_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE,
    CONSTRAINT FK_user_account_role FOREIGN KEY (role_id)
        REFERENCES role(role_id) ON DELETE NO ACTION
);

-- ============================================================
-- ADMIN
-- ============================================================
CREATE TABLE admin (
    admin_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    person_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    admin_code NVARCHAR(50) NOT NULL UNIQUE,
    position NVARCHAR(200),
    admin_status NVARCHAR(20) DEFAULT 'active' CHECK (admin_status IN ('active', 'inactive')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_admin_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE
);

-- ============================================================
-- OTP & REFRESH TOKEN
-- ============================================================
CREATE TABLE user_otp (
    otp_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    otp_code NVARCHAR(6) NOT NULL,
    expired_at DATETIME2 NOT NULL,
    is_used BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT FK_user_otp_user_account FOREIGN KEY (user_id) 
        REFERENCES user_account(user_id) ON DELETE CASCADE
);

CREATE TABLE user_refresh_token (
    token_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    refresh_token NVARCHAR(500) NOT NULL,
    expires_at DATETIME2 NOT NULL,
    is_revoked BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT FK_user_refresh_token_user_account FOREIGN KEY (user_id) 
        REFERENCES user_account(user_id) ON DELETE CASCADE
);

-- ============================================================
-- BUILDING & ROOM
-- ============================================================
CREATE TABLE building (
    building_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    building_name NVARCHAR(200) NOT NULL,
    building_code NVARCHAR(50) NOT NULL UNIQUE,
    address NVARCHAR(500),
    building_status NVARCHAR(20) DEFAULT 'active' CHECK (building_status IN ('active', 'inactive', 'maintenance')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

CREATE TABLE room (
    room_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    room_code NVARCHAR(50) NOT NULL UNIQUE,
    room_name NVARCHAR(200) NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    room_type NVARCHAR(30) NOT NULL 
        CHECK (room_type IN (
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
        )),
    building_id UNIQUEIDENTIFIER NOT NULL,
    room_status NVARCHAR(20) DEFAULT 'active' CHECK (room_status IN ('active', 'inactive', 'maintenance')),

    room_picture_path NVARCHAR(500) NULL,  -- <--- new column for picture path

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    
    CONSTRAINT FK_room_building FOREIGN KEY (building_id) 
        REFERENCES building(building_id) ON DELETE CASCADE
);

-- ============================================================
-- ROOM_AMENITY
-- ============================================================
CREATE TABLE room_amenity (
    amenity_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    amenity_name NVARCHAR(100) NOT NULL UNIQUE,
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

-- ============================================================
-- ROOM_AMENITY_MAPPING
-- ============================================================
CREATE TABLE room_amenity_mapping (
    room_amenity_mapping_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    room_id UNIQUEIDENTIFIER NOT NULL,
    amenity_id UNIQUEIDENTIFIER NOT NULL,
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    
    CONSTRAINT FK_room_amenity_mapping_room FOREIGN KEY (room_id)
        REFERENCES room(room_id) ON DELETE CASCADE,
    CONSTRAINT FK_room_amenity_mapping_amenity FOREIGN KEY (amenity_id)
        REFERENCES room_amenity(amenity_id) ON DELETE CASCADE,
    CONSTRAINT UQ_room_amenity_mapping UNIQUE (room_id, amenity_id)
);

-- ============================================================
-- ACADEMIC YEAR
-- ============================================================
CREATE TABLE academic_year (
    academic_year_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    year_name NVARCHAR(50) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    academic_year_status NVARCHAR(20) NOT NULL DEFAULT 'active' CHECK (academic_year_status IN ('active', 'inactive', 'completed')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    
    CONSTRAINT CHK_academic_year_dates CHECK (end_date > start_date)
);

-- ============================================================
-- SEMESTER
-- ============================================================
CREATE TABLE semester (
    semester_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    semester_name NVARCHAR(100) NOT NULL,
    academic_year_id UNIQUEIDENTIFIER NOT NULL,
    semester_type NVARCHAR(20) NOT NULL CHECK (semester_type IN ('fall', 'spring', 'summer')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    registration_start_date DATE NOT NULL,
    registration_end_date DATE NOT NULL,
    semester_status NVARCHAR(20) DEFAULT 'active' CHECK (semester_status IN ('active', 'inactive', 'completed')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_semester_academic_year FOREIGN KEY (academic_year_id) 
        REFERENCES academic_year(academic_year_id) ON DELETE CASCADE,
    CONSTRAINT CHK_semester_dates CHECK (end_date > start_date),
    CONSTRAINT CHK_semester_registration_dates CHECK (registration_end_date > registration_start_date),
    CONSTRAINT CHK_semester_registration_before_start CHECK (registration_end_date <= start_date)
);

CREATE TABLE division (
    division_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    division_name NVARCHAR(200) NOT NULL,
    division_code NVARCHAR(50) NOT NULL UNIQUE,
    division_status NVARCHAR(20) DEFAULT 'active' CHECK (division_status IN ('active','inactive')),
    dean_id UNIQUEIDENTIFIER NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

-- ============================================================
-- FACULTY
-- ============================================================
CREATE TABLE faculty (
    faculty_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    faculty_name NVARCHAR(200) NOT NULL,
    faculty_code NVARCHAR(50) NOT NULL UNIQUE,
    dean_id UNIQUEIDENTIFIER NULL,
    faculty_status NVARCHAR(20) DEFAULT 'active' CHECK (faculty_status IN ('active','inactive')),
    division_id UNIQUEIDENTIFIER NOT NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_faculty_division FOREIGN KEY (division_id)
        REFERENCES division(division_id) ON DELETE CASCADE
);

-- ============================================================
-- DEPARTMENT
-- ============================================================
CREATE TABLE department (
    department_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    department_name NVARCHAR(200) NOT NULL,
    department_code NVARCHAR(50) NOT NULL UNIQUE,
    faculty_id UNIQUEIDENTIFIER NOT NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_department_faculty FOREIGN KEY (faculty_id) 
        REFERENCES faculty(faculty_id) ON DELETE CASCADE
);

-- ============================================================
-- INSTRUCTOR
-- ============================================================
CREATE TABLE instructor (
    instructor_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    person_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    instructor_code NVARCHAR(50) NOT NULL UNIQUE,
    degree NVARCHAR(50) CHECK (degree IN ('PhD', 'Master', 'Bachelor', 'Engineer')),
    specialization NVARCHAR(500),
    faculty_id UNIQUEIDENTIFIER NULL,
    hire_date DATE,
    employment_status NVARCHAR(20) DEFAULT 'active' CHECK (employment_status IN ('active', 'inactive', 'retired', 'on_leave')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_instructor_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE,
    CONSTRAINT FK_instructor_faculty FOREIGN KEY (faculty_id) 
        REFERENCES faculty(faculty_id) ON DELETE SET NULL
);

-- Add circular foreign keys
ALTER TABLE division 
    ADD CONSTRAINT FK_division_dean_instructor 
    FOREIGN KEY (dean_id) REFERENCES instructor(instructor_id) ON DELETE SET NULL;

-- Add circular foreign keys
ALTER TABLE faculty 
    ADD CONSTRAINT FK_faculty_dean_instructor 
    FOREIGN KEY (dean_id) REFERENCES instructor(instructor_id) ON DELETE SET NULL;


-- ============================================================
-- SUBJECT
-- ============================================================
CREATE TABLE subject (
    subject_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    subject_name NVARCHAR(200) NOT NULL UNIQUE,
    subject_code NVARCHAR(50) NOT NULL UNIQUE,
    credits INT NOT NULL CHECK (credits > 0),
    theory_hours INT DEFAULT 0 CHECK (theory_hours >= 0),
    practice_hours INT DEFAULT 0 CHECK (practice_hours >= 0),
    is_general BIT DEFAULT 0,
    department_id UNIQUEIDENTIFIER NOT NULL,
    prerequisite_subject_id UNIQUEIDENTIFIER NULL,
    subject_status NVARCHAR(20) DEFAULT 'active' CHECK (subject_status IN ('active', 'inactive', 'archived')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_subject_department FOREIGN KEY (department_id) 
        REFERENCES department(department_id) ON DELETE CASCADE,
    CONSTRAINT FK_subject_prerequisite_subject FOREIGN KEY (prerequisite_subject_id) 
        REFERENCES subject(subject_id) ON DELETE NO ACTION
);

-- ============================================================
-- TRAINING SYSTEM (Hệ đào tạo)
-- ============================================================
CREATE TABLE training_system (
    training_system_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    training_system_name NVARCHAR(100) NOT NULL UNIQUE,  -- e.g., Regular, Part-time, Distance, Transfer
    description NVARCHAR(500),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);



-- ============================================================
-- CURRICULUM (Chương trình Đào tạo - Thực thể chính)
-- ============================================================
CREATE TABLE curriculum (
    curriculum_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    curriculum_code NVARCHAR(50) NOT NULL,
    curriculum_name NVARCHAR(500) NOT NULL,
    department_id UNIQUEIDENTIFIER NOT NULL,
    applied_year INT NOT NULL CHECK (applied_year BETWEEN 1900 AND 2100),
    version_number INT NOT NULL CHECK (version_number > 0),   -- Bắt buộc > 0

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_curriculum_department FOREIGN KEY (department_id) 
        REFERENCES department(department_id) ON DELETE NO ACTION,

    -- Mỗi curriculum_code + version_number là duy nhất
    CONSTRAINT UQ_curriculum_code_version UNIQUE (curriculum_code, version_number)
);

CREATE TABLE curriculum_detail (
    curriculum_detail_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    curriculum_id UNIQUEIDENTIFIER NOT NULL,
    subject_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Các trường thể hiện vị trí Môn học trong CTĐT
    academic_year_index INT NOT NULL CHECK (academic_year_index IN (1, 2, 3, 4)), -- Năm học thứ 1, 2, 3, 4
    semester_index INT NOT NULL CHECK (semester_index IN (1, 2, 3)),   -- Học kỳ 1, 2, 3... (Giả định có 3 HK/năm)
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_curriculum_detail_curriculum FOREIGN KEY (curriculum_id) 
        REFERENCES curriculum(curriculum_id) ON DELETE CASCADE,
    CONSTRAINT FK_curriculum_detail_subject FOREIGN KEY (subject_id) 
        REFERENCES subject(subject_id) ON DELETE NO ACTION,

    -- Đảm bảo một môn học chỉ xuất hiện một lần trong một CTĐT
    CONSTRAINT UQ_curriculum_subject UNIQUE (curriculum_id, subject_id)
);

-- ============================================================
-- CLASS (Updated)
-- ============================================================
CREATE TABLE class (
    class_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    class_code NVARCHAR(50) NOT NULL UNIQUE,
    class_name NVARCHAR(200) NOT NULL,
    department_id UNIQUEIDENTIFIER NOT NULL,
    advisor_instructor_id UNIQUEIDENTIFIER NULL,
    training_system_id UNIQUEIDENTIFIER NOT NULL,  -- new column
    start_academic_year_id UNIQUEIDENTIFIER NOT NULL,
    end_academic_year_id UNIQUEIDENTIFIER NOT NULL,
    curriculum_desc_pdf NVARCHAR(1000),
    class_status NVARCHAR(20) DEFAULT 'active' CHECK (class_status IN ('active', 'inactive', 'graduated')),
    curriculum_id UNIQUEIDENTIFIER NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_class_department FOREIGN KEY (department_id) 
        REFERENCES department(department_id) ON DELETE CASCADE,
    CONSTRAINT FK_class_advisor_instructor FOREIGN KEY (advisor_instructor_id)
        REFERENCES instructor(instructor_id) ON DELETE SET NULL,
    CONSTRAINT FK_class_training_system FOREIGN KEY (training_system_id)
        REFERENCES training_system(training_system_id) ON DELETE NO ACTION,
    CONSTRAINT FK_class_start_academic_year FOREIGN KEY (start_academic_year_id) 
        REFERENCES academic_year(academic_year_id) ON DELETE NO ACTION,
    CONSTRAINT FK_class_end_academic_year FOREIGN KEY (end_academic_year_id) 
        REFERENCES academic_year(academic_year_id) ON DELETE NO ACTION,
    CONSTRAINT FK_class_curriculum FOREIGN KEY (curriculum_id) 
        REFERENCES curriculum(curriculum_id) ON DELETE SET NULL 
);

-- ============================================================
-- STUDENT
-- ============================================================
CREATE TABLE student (
    student_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    person_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    student_code NVARCHAR(50) NOT NULL UNIQUE,
    class_id UNIQUEIDENTIFIER NULL,
    enrollment_status NVARCHAR(20) DEFAULT 'active' CHECK (enrollment_status IN ('active', 'inactive', 'qualified', 'graduated', 'dropped_out', 'suspended')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_student_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE,
    CONSTRAINT FK_student_class FOREIGN KEY (class_id) 
        REFERENCES class(class_id) ON DELETE SET NULL
);

-- ============================================================
-- COURSE
-- ============================================================
CREATE TABLE course (
    course_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    subject_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL,
    course_code NVARCHAR(50) NOT NULL,
    fee_per_credit NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (fee_per_credit >= 0),
    course_status NVARCHAR(20) DEFAULT 'active' CHECK (course_status IN ('active', 'inactive', 'completed', 'cancelled')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_course_subject FOREIGN KEY (subject_id) 
        REFERENCES subject(subject_id) ON DELETE CASCADE,
    CONSTRAINT FK_course_semester FOREIGN KEY (semester_id) 
        REFERENCES semester(semester_id) ON DELETE CASCADE,
    CONSTRAINT UQ_course_code UNIQUE (course_code)
);

-- ============================================================
-- COURSE CLASS
-- ============================================================
CREATE TABLE course_class (
    course_class_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_id UNIQUEIDENTIFIER NOT NULL,
    instructor_id UNIQUEIDENTIFIER NULL,
    room_id UNIQUEIDENTIFIER NOT NULL,
    course_class_code NVARCHAR(50) NOT NULL,
    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    max_students INT NOT NULL CHECK (max_students > 0),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 2 AND 8),
    start_period INT NOT NULL CHECK (start_period BETWEEN 1 AND 12),
    end_period INT NOT NULL CHECK (end_period BETWEEN 1 AND 12),
    course_class_status NVARCHAR(20) DEFAULT 'active' 
        CHECK (course_class_status IN ('active', 'inactive', 'completed', 'cancelled')),

    -- Grade submission workflow
    grade_submission_status NVARCHAR(50) DEFAULT 'draft' 
        CHECK (grade_submission_status IN ('draft', 'pending', 'approved')),
    grade_submitted_at DATETIME2 NULL,
    grade_approved_at DATETIME2 NULL,
    grade_approved_by UNIQUEIDENTIFIER NULL,
    grade_submission_note NVARCHAR(MAX) NULL,
    grade_approval_note NVARCHAR(MAX) NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_course_class_course FOREIGN KEY (course_id) 
        REFERENCES course(course_id) ON DELETE CASCADE,
    CONSTRAINT FK_course_class_instructor FOREIGN KEY (instructor_id) 
        REFERENCES instructor(instructor_id) ON DELETE SET NULL,
    CONSTRAINT FK_course_class_room FOREIGN KEY (room_id) 
        REFERENCES room(room_id) ON DELETE NO ACTION,

    CONSTRAINT CHK_course_class_periods CHECK (end_period >= start_period),

    -- Custom constraint: start_period and end_period must belong to the same valid range
    CONSTRAINT CHK_course_class_period_block CHECK (
        (
            start_period BETWEEN 1 AND 5 AND end_period BETWEEN 1 AND 5
        )
        OR (
            start_period BETWEEN 6 AND 9 AND end_period BETWEEN 6 AND 9
        )
        OR (
            start_period BETWEEN 10 AND 12 AND end_period BETWEEN 10 AND 12
        )
    ),

    CONSTRAINT CHK_course_class_dates CHECK (date_end > date_start),
    CONSTRAINT UQ_course_class_code UNIQUE (course_class_code)
);

-- ============================================================
-- STUDENT ENROLLMENT
-- ============================================================
CREATE TABLE student_enrollment (
    enrollment_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    enrollment_date DATE DEFAULT GETDATE(),
    enrollment_status NVARCHAR(20) DEFAULT 'registered' 
        CHECK (enrollment_status IN ('registered', 'dropped', 'completed', 'cancelled')),
    cancellation_date DATE NULL,
    cancellation_reason NVARCHAR(500) NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
	is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT UQ_student_enrollment_course_class UNIQUE (student_id, course_class_id),
    CONSTRAINT FK_student_enrollment_student FOREIGN KEY (student_id) 
        REFERENCES student(student_id) ON DELETE CASCADE,
    CONSTRAINT FK_student_enrollment_course_class FOREIGN KEY (course_class_id) 
        REFERENCES course_class(course_class_id) ON DELETE CASCADE
);

-- ============================================================
-- ENROLLMENT DRAFT GRADE (Draft grades for each student)
-- ============================================================
CREATE TABLE enrollment_draft_grade (
    draft_grade_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    enrollment_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    
    -- Draft grades (editable by instructors)
    attendance_grade_draft NUMERIC(4,2) CHECK (attendance_grade_draft BETWEEN 0 AND 10),
    midterm_grade_draft NUMERIC(4,2) CHECK (midterm_grade_draft BETWEEN 0 AND 10),
    final_grade_draft NUMERIC(4,2) CHECK (final_grade_draft BETWEEN 0 AND 10),
    
    -- Grade note for instructor comments
    grade_note NVARCHAR(500) NULL,
    
    updated_at DATETIME2 NULL,
    
    CONSTRAINT FK_enrollment_draft_grade_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES student_enrollment(enrollment_id) ON DELETE CASCADE
);

-- ============================================================
-- ENROLLMENT GRADE VERSION (Version history of grade submissions)
-- ============================================================
CREATE TABLE enrollment_grade_version (
    grade_version_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Version information
    version_number INT NOT NULL CHECK (version_number > 0),
    
    -- Submission workflow
    version_status NVARCHAR(50) DEFAULT 'pending' 
        CHECK (version_status IN ('pending', 'approved', 'rejected')),
    
    -- Submission info
    submitted_by UNIQUEIDENTIFIER NULL, -- Instructor who submitted
    submitted_at DATETIME2 NULL,
    submission_note NVARCHAR(MAX) NULL,
    
    -- Approval info
    approved_by UNIQUEIDENTIFIER NULL, -- Admin who approved/rejected
    approved_at DATETIME2 NULL,
    approval_note NVARCHAR(MAX) NULL,
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT FK_enrollment_grade_version_course_class FOREIGN KEY (course_class_id)
        REFERENCES course_class(course_class_id) ON DELETE CASCADE,
    CONSTRAINT FK_enrollment_grade_version_submitted_by FOREIGN KEY (submitted_by)
        REFERENCES instructor(instructor_id) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT FK_enrollment_grade_version_approved_by FOREIGN KEY (approved_by)
        REFERENCES admin(admin_id) ON DELETE NO ACTION ON UPDATE NO ACTION,
    
    -- Ensure unique version numbers per course class
    CONSTRAINT UQ_enrollment_grade_version UNIQUE (course_class_id, version_number)
);

-- ============================================================
-- ENROLLMENT GRADE DETAIL (Individual student grades per version)
-- ============================================================
CREATE TABLE enrollment_grade_detail (
    grade_detail_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    grade_version_id UNIQUEIDENTIFIER NOT NULL,
    enrollment_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Official grades for this version
    attendance_grade NUMERIC(4,2) CHECK (attendance_grade BETWEEN 0 AND 10),
    midterm_grade NUMERIC(4,2) CHECK (midterm_grade BETWEEN 0 AND 10),
    final_grade NUMERIC(4,2) CHECK (final_grade BETWEEN 0 AND 10),
    
    -- Grade note for instructor comments
    grade_note NVARCHAR(500) NULL,
    
    CONSTRAINT FK_enrollment_grade_detail_version FOREIGN KEY (grade_version_id)
        REFERENCES enrollment_grade_version(grade_version_id) ON DELETE CASCADE,
    CONSTRAINT FK_enrollment_grade_detail_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES student_enrollment(enrollment_id) ON DELETE NO ACTION ON UPDATE NO ACTION,
    
    -- Ensure one grade record per student per version
    CONSTRAINT UQ_enrollment_grade_detail UNIQUE (grade_version_id, enrollment_id)
);

-- ============================================================
-- SCHEDULE CHANGE
-- ============================================================
CREATE TABLE schedule_change (
    schedule_change_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    cancelled_week INT NOT NULL CHECK (cancelled_week > 0),
    makeup_week INT CHECK (makeup_week > 0),
    makeup_date DATE NULL,
    makeup_room_id UNIQUEIDENTIFIER NULL,
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 2 AND 8),
    start_period INT NOT NULL CHECK (start_period BETWEEN 1 AND 12),
    end_period INT NOT NULL CHECK (end_period BETWEEN 1 AND 12),
    reason NVARCHAR(500),
    report_file_url NVARCHAR(1000) NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_schedule_change_course_class FOREIGN KEY (course_class_id) 
        REFERENCES course_class(course_class_id) ON DELETE CASCADE,
    CONSTRAINT FK_schedule_change_makeup_room FOREIGN KEY (makeup_room_id) 
        REFERENCES room(room_id) ON DELETE NO ACTION,

    CONSTRAINT CHK_schedule_change_periods CHECK (end_period >= start_period),

    -- Custom constraint: start_period and end_period must be in the same valid range
    CONSTRAINT CHK_schedule_change_period_block CHECK (
        (
            start_period BETWEEN 1 AND 5 AND end_period BETWEEN 1 AND 5
        )
        OR (
            start_period BETWEEN 6 AND 9 AND end_period BETWEEN 6 AND 9
        )
        OR (
            start_period BETWEEN 10 AND 12 AND end_period BETWEEN 10 AND 12
        )
    )
);

-- ============================================================
-- DOCUMENT
-- ============================================================
CREATE TABLE document (
    document_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_class_id UNIQUEIDENTIFIER NOT NULL,
	file_title NVARCHAR(500) NOT NULL,
    file_name NVARCHAR(500) NOT NULL,
	document_type NVARCHAR(20) NOT NULL CHECK (document_type IN (N'Bài tập', N'Tài liệu', N'Slide', N'Bài LAB')),
    file_path NVARCHAR(1000) NOT NULL,
    file_type NVARCHAR(20) CHECK (file_type IN ('pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'zip', 'rar')),
    file_size BIGINT CHECK (file_size > 0),
    uploaded_by UNIQUEIDENTIFIER NULL,
    description NVARCHAR(1000),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_document_course_class FOREIGN KEY (course_class_id) 
        REFERENCES course_class(course_class_id) ON DELETE CASCADE,
    CONSTRAINT FK_document_uploaded_by_instructor FOREIGN KEY (uploaded_by) 
        REFERENCES instructor(instructor_id) ON DELETE SET NULL
);

-- ============================================================
-- NOTIFICATION
-- ============================================================
CREATE TABLE notification_schedule (
    schedule_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    notification_type NVARCHAR(50) NOT NULL CHECK (notification_type IN ('event', 'tuition', 'schedule', 'important')),
    title NVARCHAR(500) NOT NULL,
    content NVARCHAR(MAX),
    notice_message NVARCHAR(1000) NULL,
    scheduled_date DATETIME2 NOT NULL,
    visible_from DATETIME2 NOT NULL,
    is_read BIT NOT NULL DEFAULT 0,
    target_type NVARCHAR(50) NOT NULL CHECK (target_type IN ('all', 'all_students', 'all_instructors', 'class', 'faculty', 'instructor', 'student')),
    target_id UNIQUEIDENTIFIER NULL,
    created_by_user UNIQUEIDENTIFIER NOT NULL,
    status NVARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'cancelled')),
    event_location NVARCHAR(100) NULL,
    event_start_date DATETIME2 NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_notification_creator FOREIGN KEY (created_by_user) 
        REFERENCES user_account(user_id) ON DELETE NO ACTION
);

-- ============================================================
-- EXAM (Course-level exam definition)
-- ============================================================
CREATE TABLE exam (
    exam_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_id UNIQUEIDENTIFIER NOT NULL,
    exam_format NVARCHAR(50) NOT NULL CHECK (exam_format IN ('multiple_choice', 'essay', 'practical', 'oral', 'mixed')),
    exam_type NVARCHAR(20) DEFAULT 'final' CHECK (exam_type IN ('midterm', 'final', 'makeup', 'quiz')),
    notes NVARCHAR(500),
    num_exam_codes_needed INT NOT NULL CHECK (num_exam_codes_needed > 0),
    exam_status NVARCHAR(20) DEFAULT 'draft' CHECK (exam_status IN ('draft', 'ready', 'published', 'cancelled')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_exam_course FOREIGN KEY (course_id) 
        REFERENCES course(course_id) ON DELETE CASCADE
);

-- ============================================================
-- EXAM ENTRY (Individual exam submissions from instructors)
-- ============================================================
CREATE TABLE exam_entry (
    exam_entry_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    exam_id UNIQUEIDENTIFIER NOT NULL,
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    
    entry_code NVARCHAR(10) NULL, -- Assigned when picked (A, B, C, etc.)
    display_name NVARCHAR(200) NOT NULL,
    question_file_path NVARCHAR(1000) NOT NULL,
    answer_file_path NVARCHAR(1000) NOT NULL,
    duration_minutes INT NOT NULL CHECK (duration_minutes > 0),
    
    is_picked BIT NOT NULL DEFAULT 0,
    entry_status NVARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (entry_status IN ('pending', 'approved', 'rejected')),
    
    rejection_reason NVARCHAR(500) NULL,
    reviewed_by UNIQUEIDENTIFIER NULL,
    reviewed_at DATETIME2 NULL,
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    
    CONSTRAINT FK_exam_entry_exam FOREIGN KEY (exam_id) 
        REFERENCES exam(exam_id) ON DELETE CASCADE,
    CONSTRAINT FK_exam_entry_course_class FOREIGN KEY (course_class_id) 
        REFERENCES course_class(course_class_id),
    CONSTRAINT FK_exam_entry_reviewed_by FOREIGN KEY (reviewed_by)
        REFERENCES admin(admin_id) ON DELETE SET NULL,
    
    -- Only picked entries can have entry_code
    CONSTRAINT CHK_entry_code_when_picked CHECK (
        (is_picked = 0 AND entry_code IS NULL) OR 
        (is_picked = 1 AND entry_code IS NOT NULL)
    ),
    
    -- Can only be picked if approved
    CONSTRAINT CHK_picked_must_be_approved CHECK (
        (is_picked = 0) OR 
        (is_picked = 1 AND entry_status = 'approved')
    )
);

-- ============================================================
-- EXAM CLASS (Exam schedule for specific course class)
-- ============================================================
CREATE TABLE exam_class (
    exam_class_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    exam_id UNIQUEIDENTIFIER NOT NULL,
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    room_id UNIQUEIDENTIFIER NOT NULL,
    monitor_instructor_id UNIQUEIDENTIFIER NULL,
    start_time DATETIME2 NOT NULL,
    duration_minutes INT NOT NULL CHECK (duration_minutes > 0),
    exam_status NVARCHAR(20) DEFAULT 'scheduled' CHECK (exam_status IN ('scheduled', 'completed', 'cancelled')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_exam_class_exam FOREIGN KEY (exam_id) 
        REFERENCES exam(exam_id) ON DELETE NO ACTION,
    CONSTRAINT FK_exam_class_course_class FOREIGN KEY (course_class_id) 
        REFERENCES course_class(course_class_id) ON DELETE CASCADE,
    CONSTRAINT FK_exam_class_room FOREIGN KEY (room_id) 
        REFERENCES room(room_id) ON DELETE NO ACTION,
    CONSTRAINT FK_exam_class_monitor FOREIGN KEY (monitor_instructor_id) 
        REFERENCES instructor(instructor_id) ON DELETE SET NULL
);

-- ============================================================
-- STUDENT HEALTH INSURANCE
-- ============================================================
CREATE TABLE student_health_insurance (
    insurance_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    academic_year_id UNIQUEIDENTIFIER NOT NULL,
    insurance_fee NUMERIC(15,2) NOT NULL CHECK (insurance_fee >= 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    insurance_status NVARCHAR(20) DEFAULT 'active' CHECK (insurance_status IN ('active', 'expired', 'cancelled')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_student_health_insurance_student FOREIGN KEY (student_id) 
        REFERENCES student(student_id) ON DELETE CASCADE,
    CONSTRAINT FK_student_health_insurance_academic_year FOREIGN KEY (academic_year_id) 
        REFERENCES academic_year(academic_year_id) ON DELETE CASCADE,
    CONSTRAINT UQ_student_academic_year_insurance UNIQUE (student_id, academic_year_id),
    CONSTRAINT CHK_student_health_insurance_dates CHECK (end_date > start_date)
);

-- ============================================================
-- PAYMENT_ENROLLMENT (Course Tuition Payments)
-- ============================================================
CREATE TABLE payment_enrollment (
    payment_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL,
    payment_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    transaction_reference NVARCHAR(200), -- Bank transaction code or receipt number
    payment_status NVARCHAR(20) DEFAULT 'pending'
         CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded')),
    notes NVARCHAR(500),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_payment_enrollment_student FOREIGN KEY (student_id)
        REFERENCES student(student_id) ON DELETE NO ACTION,
    CONSTRAINT FK_payment_enrollment_semester FOREIGN KEY (semester_id)
        REFERENCES semester(semester_id) ON DELETE NO ACTION
);

-- ============================================================
-- PAYMENT_ENROLLMENT_DETAIL (SPECIFY WHICH COURSES THIS PAYMENT PAYS FOR)
-- ============================================================
CREATE TABLE payment_enrollment_detail (
    payment_enrollment_detail_ID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    payment_id UNIQUEIDENTIFIER NOT NULL,
    enrollment_id UNIQUEIDENTIFIER NOT NULL,
    amount_paid NUMERIC(18,2) NOT NULL DEFAULT 0,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,

    CONSTRAINT FK_payment_mapping_payment FOREIGN KEY (payment_id)
        REFERENCES payment_enrollment(payment_id) ON DELETE CASCADE,
    CONSTRAINT FK_payment_mapping_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES student_enrollment(enrollment_id) ON DELETE CASCADE,
    CONSTRAINT UQ_payment_mapping UNIQUE(payment_id, enrollment_id)
);


-- ============================================================
-- PAYMENT_INSURANCE (Health Insurance Payments)
-- ============================================================
CREATE TABLE payment_insurance (
    payment_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    insurance_id UNIQUEIDENTIFIER NOT NULL,
    payment_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    payment_status NVARCHAR(20) DEFAULT 'pending'
         CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded')),
    notes NVARCHAR(500),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_payment_insurance_insurance FOREIGN KEY (insurance_id) 
        REFERENCES student_health_insurance(insurance_id) ON DELETE CASCADE
);

-- ============================================================
-- ROOM BOOKING
-- ============================================================
CREATE TABLE room_booking (
    booking_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    room_id UNIQUEIDENTIFIER NOT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    booked_by UNIQUEIDENTIFIER NOT NULL,
    purpose NVARCHAR(500),
    student_count INT NOT NULL DEFAULT 0,
    booking_status NVARCHAR(20) DEFAULT 'confirmed' CHECK (booking_status IN ('pending', 'confirmed', 'cancelled', 'completed')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_room_booking_room FOREIGN KEY (room_id) 
        REFERENCES room(room_id) ON DELETE CASCADE,
    CONSTRAINT FK_room_booking_user FOREIGN KEY (booked_by) 
        REFERENCES user_account(user_id) ON DELETE NO ACTION,
    CONSTRAINT CHK_room_booking_times CHECK (end_time > start_time)
);
-- ============================================================
-- REGULATION
-- ============================================================
CREATE TABLE regulation (
    regulation_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    regulation_name NVARCHAR(200) NOT NULL,
    target NVARCHAR(20) NOT NULL CHECK (target IN ('student', 'instructor')),
    pdf_file_path NVARCHAR(1000) NOT NULL,
    regulation_description NVARCHAR(1000) NOT NULL,
	expire_date DATE NULL,
    created_by_admin UNIQUEIDENTIFIER NOT NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_regulation_created_by_admin FOREIGN KEY (created_by_admin) 
        REFERENCES admin(admin_id) ON DELETE NO ACTION
);

-- ============================================================
-- STUDENT_VERIFICATION_REQUEST
-- ============================================================
CREATE TABLE student_verification_request (
    verification_request_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    language NVARCHAR(2) NOT NULL DEFAULT 'vi' CHECK (language IN ('vi', 'en')),
    reason NVARCHAR(500) NOT NULL,
    request_status NVARCHAR(20) DEFAULT 'pending' CHECK (request_status IN ('pending', 'approved', 'rejected', 'completed')),
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_verification_request_student FOREIGN KEY (student_id)
        REFERENCES student(student_id) ON DELETE CASCADE
);

-- ============================================================
-- PAYMENT_POSTPONEMENT_REQUEST
-- ============================================================
CREATE TABLE payment_postponement_request (
    request_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL,
    request_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    reason NVARCHAR(500) NOT NULL,
    request_status NVARCHAR(20) DEFAULT 'pending' CHECK (request_status IN ('pending', 'approved', 'rejected', 'cancelled')),
    new_payment_deadline DATE NULL,
    
    -- Admin who reviewed/processed the request
    reviewed_by UNIQUEIDENTIFIER NULL,
    reviewed_at DATETIME2 NULL,
    review_notes NVARCHAR(500) NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_payment_postponement_student FOREIGN KEY (student_id)
        REFERENCES student(student_id) ON DELETE CASCADE,
    CONSTRAINT FK_payment_postponement_semester FOREIGN KEY (semester_id) 
        REFERENCES semester(semester_id) ON DELETE CASCADE,
    CONSTRAINT FK_payment_postponement_reviewed_by FOREIGN KEY (reviewed_by)
        REFERENCES admin(admin_id) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT CHK_reviewed_at_when_processed CHECK (
        (request_status = 'pending' AND reviewed_by IS NULL AND reviewed_at IS NULL) OR
        (request_status IN ('approved', 'rejected') AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL) OR
        (request_status = 'cancelled')
    )
);

-- ============================================================
-- NOTE
-- ============================================================
CREATE TABLE note (
    note_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    content NVARCHAR(MAX) NOT NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
);

-- NOTIFICATION USER READ (Lưu trạng thái đọc của từng người dùng)
-- ============================================================
CREATE TABLE notification_user_read (
    notification_user_read_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    schedule_id UNIQUEIDENTIFIER NOT NULL,
    user_id UNIQUEIDENTIFIER NOT NULL,
    read_at DATETIME2 NOT NULL DEFAULT GETDATE(),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),

    CONSTRAINT FK_notification_user_read_schedule FOREIGN KEY (schedule_id) 
        REFERENCES notification_schedule(schedule_id) ON DELETE CASCADE,
    CONSTRAINT FK_notification_user_read_user FOREIGN KEY (user_id) 
        REFERENCES user_account(user_id) ON DELETE CASCADE,
    
    -- Đảm bảo mỗi user chỉ có 1 bản ghi đọc cho mỗi thông báo
    CONSTRAINT UQ_notification_user_read UNIQUE (schedule_id, user_id)
);

-- Index để tối ưu truy vấn
CREATE INDEX idx_notification_user_read_user ON notification_user_read(user_id);
CREATE INDEX idx_notification_user_read_schedule ON notification_user_read(schedule_id);

-- ============================================================
-- THEME CONFIGURATIONS
-- ============================================================
CREATE TABLE theme_configurations (
    theme_config_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    
    -- Metadata
    theme_name NVARCHAR(200) NOT NULL,
    description NVARCHAR(MAX),
    created_by_admin_id UNIQUEIDENTIFIER NOT NULL,
    
    -- Scope (page/component specific)
    scope_type NVARCHAR(50) NOT NULL CHECK (scope_type IN ('global', 'page', 'component')),
    scope_target NVARCHAR(200) NOT NULL DEFAULT '', -- Dùng '' thay vì NULL
    
    -- Theme variables (JSON format)
    theme_variables NVARCHAR(MAX) NOT NULL,
    
    -- Standard audit fields
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    
    -- Constraints
    CONSTRAINT FK_theme_created_by FOREIGN KEY (created_by_admin_id)
        REFERENCES dbo.admin(admin_id) ON DELETE NO ACTION,
    CONSTRAINT CHK_theme_name_not_empty CHECK (LEN(TRIM(theme_name)) > 0),
    CONSTRAINT CHK_theme_variables_json CHECK (ISJSON(theme_variables) = 1)
);

-- Indexes
CREATE INDEX idx_theme_active ON theme_configurations(is_active) WHERE is_active = 1;
CREATE INDEX idx_theme_scope ON theme_configurations(scope_type, scope_target);
CREATE INDEX idx_theme_created_by ON theme_configurations(created_by_admin_id);

-- Unique constraint: chỉ 1 theme active mỗi scope
CREATE UNIQUE INDEX UQ_theme_scope_active 
ON theme_configurations(scope_type, scope_target)
WHERE is_active = 1 AND is_deleted = 0;

-- ============================================================
-- THEME HISTORY
-- ============================================================
CREATE TABLE theme_history (
    theme_history_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    theme_config_id UNIQUEIDENTIFIER NOT NULL,
    action NVARCHAR(50) NOT NULL CHECK (action IN ('created', 'updated', 'activated', 'deactivated', 'deleted')),
    changed_by_admin_id UNIQUEIDENTIFIER NOT NULL,
    previous_values NVARCHAR(MAX),
    new_values NVARCHAR(MAX),
    change_reason NVARCHAR(500),
    
    -- Standard audit fields
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    
    -- Foreign key constraints
    CONSTRAINT FK_theme_history_config FOREIGN KEY (theme_config_id)
        REFERENCES theme_configurations(theme_config_id) ON DELETE CASCADE,
    CONSTRAINT FK_theme_history_admin FOREIGN KEY (changed_by_admin_id)
        REFERENCES dbo.admin(admin_id) ON DELETE NO ACTION,
    
    -- Additional constraints
    CONSTRAINT CHK_theme_history_action_not_empty CHECK (LEN(TRIM(action)) > 0),
    CONSTRAINT CHK_theme_history_previous_json CHECK (previous_values IS NULL OR ISJSON(previous_values) = 1),
    CONSTRAINT CHK_theme_history_new_json CHECK (new_values IS NULL OR ISJSON(new_values) = 1)
);

-- Indexes
CREATE INDEX idx_theme_history_config ON theme_history(theme_config_id);
CREATE INDEX idx_theme_history_admin ON theme_history(changed_by_admin_id);
CREATE INDEX idx_theme_history_action ON theme_history(action);
CREATE INDEX idx_theme_history_created ON theme_history(created_at);

CREATE TABLE schedule_change_request (
    schedule_change_request_id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    cancelled_week INT NOT NULL,
    makeup_week INT NULL,
    makeup_date DATE NULL,
    makeup_room_id UNIQUEIDENTIFIER NULL,
    day_of_week INT NOT NULL,
    start_period INT NOT NULL,
    end_period INT NOT NULL,
    reason NVARCHAR(500) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending|approved|rejected
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER NULL,
    reviewed_at DATETIME NULL,
    reviewed_by UNIQUEIDENTIFIER NULL,
    review_note NVARCHAR(500) NULL,
    is_active BIT NOT NULL DEFAULT 1,
    is_deleted BIT NOT NULL DEFAULT 0
);

ALTER TABLE schedule_change_request
ADD CONSTRAINT FK_schedule_change_request_course_class
FOREIGN KEY (course_class_id) REFERENCES course_class(course_class_id);

ALTER TABLE schedule_change_request
ADD CONSTRAINT FK_schedule_change_request_room
FOREIGN KEY (makeup_room_id) REFERENCES room(room_id);

CREATE TABLE chat_history (
    message_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    message NVARCHAR(MAX) NOT NULL,
    session_id UNIQUEIDENTIFIER NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    INDEX IX_chat_history_user_session (user_id, session_id, created_at DESC),
    INDEX IX_chat_history_session (session_id)
);

CREATE TABLE knowledge_documents (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    title NVARCHAR(500) NOT NULL,
    content NVARCHAR(MAX) NOT NULL,
    content_summary NVARCHAR(2000),
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('faq', 'regulation', 'guide', 'course_info')),
    role_type VARCHAR(20) CHECK (role_type IN ('student', 'instructor', 'admin') OR role_type IS NULL),
    embedding_reference VARCHAR(50) DEFAULT 'pinecone' CHECK (embedding_reference IN ('pinecone', 'sqlserver')),
    metadata NVARCHAR(MAX),
    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    INDEX IX_knowledge_role_type (role_type),
    INDEX IX_knowledge_doc_type (document_type),
    INDEX IX_knowledge_created (created_at DESC)
);

-- ============================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================

-- ROLE_PERMISSION indexes
CREATE INDEX IX_role_permission_role_id ON role_permission(role_id);
CREATE INDEX IX_role_permission_permission_id ON role_permission(permission_id);

-- PERSON indexes
CREATE INDEX IX_person_email ON person(email);
CREATE INDEX IX_person_citizen_id ON person(citizen_id) WHERE citizen_id IS NOT NULL;

-- USER_ACCOUNT indexes
CREATE INDEX IX_user_account_person_id ON user_account(person_id);
CREATE INDEX IX_user_account_role_id ON user_account(role_id);
CREATE INDEX IX_user_account_username ON user_account(username);
CREATE INDEX IX_user_account_email_verified ON user_account(email_verified);
CREATE INDEX IX_user_account_account_status ON user_account(account_status) WHERE account_status = 'active';

-- ADMIN indexes
CREATE INDEX IX_admin_person_id ON admin(person_id);
CREATE INDEX IX_admin_admin_code ON admin(admin_code);

-- OTP & REFRESH TOKEN indexes
CREATE INDEX IX_user_otp_user_id ON user_otp(user_id);
CREATE INDEX IX_user_otp_expired_at ON user_otp(expired_at);
CREATE INDEX IX_user_refresh_token_user_id ON user_refresh_token(user_id);
CREATE INDEX IX_user_refresh_token_expires_at ON user_refresh_token(expires_at);

-- ROOM indexes
CREATE INDEX IX_room_building_id ON room(building_id);
CREATE INDEX IX_room_room_code ON room(room_code);
CREATE INDEX IX_room_room_type ON room(room_type);
CREATE INDEX IX_room_room_status ON room(room_status) WHERE room_status = 'active';

-- ROOM_AMENITY_MAPPING indexes
CREATE INDEX IX_room_amenity_mapping_room_id ON room_amenity_mapping(room_id);
CREATE INDEX IX_room_amenity_mapping_amenity_id ON room_amenity_mapping(amenity_id);

-- SEMESTER indexes
CREATE INDEX IX_semester_academic_year_id ON semester(academic_year_id);
CREATE INDEX IX_semester_semester_type ON semester(semester_type);
CREATE INDEX IX_semester_dates ON semester(start_date, end_date);
CREATE INDEX IX_semester_registration_dates ON semester(registration_start_date, registration_end_date);

-- DIVISION indexes
CREATE INDEX IX_division_division_code ON division(division_code);
CREATE INDEX IX_division_dean_id ON division(dean_id) WHERE dean_id IS NOT NULL;

-- FACULTY indexes
CREATE INDEX IX_faculty_faculty_code ON faculty(faculty_code);
CREATE INDEX IX_faculty_division_id ON faculty(division_id);
CREATE INDEX IX_faculty_dean_id ON faculty(dean_id) WHERE dean_id IS NOT NULL;

-- DEPARTMENT indexes
CREATE INDEX IX_department_faculty_id ON department(faculty_id);
CREATE INDEX IX_department_department_code ON department(department_code);

-- INSTRUCTOR indexes
CREATE INDEX IX_instructor_person_id ON instructor(person_id);
CREATE INDEX IX_instructor_instructor_code ON instructor(instructor_code);
CREATE INDEX IX_instructor_faculty_id ON instructor(faculty_id) WHERE faculty_id IS NOT NULL;
CREATE INDEX IX_instructor_employment_status ON instructor(employment_status) WHERE employment_status = 'active';

-- SUBJECT indexes
CREATE INDEX IX_subject_department_id ON subject(department_id);
CREATE INDEX IX_subject_subject_code ON subject(subject_code);
CREATE INDEX IX_subject_prerequisite_subject_id ON subject(prerequisite_subject_id) WHERE prerequisite_subject_id IS NOT NULL;
CREATE INDEX IX_subject_subject_status ON subject(subject_status) WHERE subject_status = 'active';

-- CURRICULUM indexes
CREATE INDEX IX_curriculum_department_id ON curriculum(department_id);
CREATE INDEX IX_curriculum_curriculum_code ON curriculum(curriculum_code);
CREATE INDEX IX_curriculum_applied_year ON curriculum(applied_year);

-- CURRICULUM_DETAIL indexes
CREATE INDEX IX_curriculum_detail_curriculum_id ON curriculum_detail(curriculum_id);
CREATE INDEX IX_curriculum_detail_subject_id ON curriculum_detail(subject_id);
CREATE INDEX IX_curriculum_detail_year_semester ON curriculum_detail(academic_year_index, semester_index);

-- CLASS indexes
CREATE INDEX IX_class_department_id ON class(department_id);
CREATE INDEX IX_class_class_code ON class(class_code);
CREATE INDEX IX_class_advisor_instructor_id ON class(advisor_instructor_id) WHERE advisor_instructor_id IS NOT NULL;
CREATE INDEX IX_class_training_system_id ON class(training_system_id);
CREATE INDEX IX_class_start_academic_year_id ON class(start_academic_year_id);
CREATE INDEX IX_class_curriculum_id ON class(curriculum_id) WHERE curriculum_id IS NOT NULL;
CREATE INDEX IX_class_class_status ON class(class_status) WHERE class_status = 'active';

-- STUDENT indexes
CREATE INDEX IX_student_person_id ON student(person_id);
CREATE INDEX IX_student_student_code ON student(student_code);
CREATE INDEX IX_student_class_id ON student(class_id) WHERE class_id IS NOT NULL;
CREATE INDEX IX_student_enrollment_status ON student(enrollment_status);

-- COURSE indexes
CREATE INDEX IX_course_subject_id ON course(subject_id);
CREATE INDEX IX_course_semester_id ON course(semester_id);
CREATE INDEX IX_course_course_status ON course(course_status) WHERE course_status = 'active';

-- COURSE_CLASS indexes
CREATE INDEX IX_course_class_course_id ON course_class(course_id);
CREATE INDEX IX_course_class_instructor_id ON course_class(instructor_id) WHERE instructor_id IS NOT NULL;
CREATE INDEX IX_course_class_room_id ON course_class(room_id);
CREATE INDEX IX_course_class_dates ON course_class(date_start, date_end);
CREATE INDEX IX_course_class_day_of_week ON course_class(day_of_week);
CREATE INDEX IX_course_class_grade_submission_status ON course_class(grade_submission_status);
CREATE INDEX IX_course_class_course_class_status ON course_class(course_class_status) WHERE course_class_status = 'active';

-- STUDENT_ENROLLMENT indexes
CREATE INDEX IX_student_enrollment_student_id ON student_enrollment(student_id);
CREATE INDEX IX_student_enrollment_course_class_id ON student_enrollment(course_class_id);
CREATE INDEX IX_student_enrollment_enrollment_date ON student_enrollment(enrollment_date);
CREATE INDEX IX_student_enrollment_enrollment_status ON student_enrollment(enrollment_status);

-- ENROLLMENT_DRAFT_GRADE indexes
CREATE INDEX IX_enrollment_draft_grade_enrollment_id ON enrollment_draft_grade(enrollment_id);

-- ENROLLMENT_GRADE_VERSION indexes
CREATE INDEX IX_enrollment_grade_version_course_class_id ON enrollment_grade_version(course_class_id);
CREATE INDEX IX_enrollment_grade_version_version_status ON enrollment_grade_version(version_status);
CREATE INDEX IX_enrollment_grade_version_submitted_by ON enrollment_grade_version(submitted_by) WHERE submitted_by IS NOT NULL;
CREATE INDEX IX_enrollment_grade_version_approved_by ON enrollment_grade_version(approved_by) WHERE approved_by IS NOT NULL;

-- ENROLLMENT_GRADE_DETAIL indexes
CREATE INDEX IX_enrollment_grade_detail_grade_version_id ON enrollment_grade_detail(grade_version_id);
CREATE INDEX IX_enrollment_grade_detail_enrollment_id ON enrollment_grade_detail(enrollment_id);

-- SCHEDULE_CHANGE indexes
CREATE INDEX IX_schedule_change_course_class_id ON schedule_change(course_class_id);
CREATE INDEX IX_schedule_change_makeup_room_id ON schedule_change(makeup_room_id) WHERE makeup_room_id IS NOT NULL;
CREATE INDEX IX_schedule_change_makeup_date ON schedule_change(makeup_date) WHERE makeup_date IS NOT NULL;

-- DOCUMENT indexes
CREATE INDEX IX_document_course_class_id ON document(course_class_id);
CREATE INDEX IX_document_uploaded_by ON document(uploaded_by) WHERE uploaded_by IS NOT NULL;
CREATE INDEX IX_document_document_type ON document(document_type);
CREATE INDEX IX_document_created_at ON document(created_at DESC);

-- NOTIFICATION_SCHEDULE indexes
CREATE INDEX IX_notification_schedule_scheduled_date ON notification_schedule(scheduled_date);
CREATE INDEX IX_notification_schedule_visible_from ON notification_schedule(visible_from);
CREATE INDEX IX_notification_schedule_notification_type ON notification_schedule(notification_type);
CREATE INDEX IX_notification_schedule_target_type ON notification_schedule(target_type);
CREATE INDEX IX_notification_schedule_target_id ON notification_schedule(target_id) WHERE target_id IS NOT NULL;
CREATE INDEX IX_notification_schedule_created_by_user ON notification_schedule(created_by_user);
CREATE INDEX IX_notification_schedule_status ON notification_schedule(status);

-- EXAM indexes
CREATE INDEX IX_exam_course_id ON exam(course_id);
CREATE INDEX IX_exam_exam_type ON exam(exam_type);
CREATE INDEX IX_exam_exam_status ON exam(exam_status);

-- EXAM_ENTRY indexes
CREATE INDEX IX_exam_entry_exam_id ON exam_entry(exam_id);
CREATE INDEX IX_exam_entry_course_class_id ON exam_entry(course_class_id);
CREATE INDEX IX_exam_entry_entry_status ON exam_entry(entry_status);
CREATE INDEX IX_exam_entry_is_picked ON exam_entry(is_picked);
CREATE INDEX IX_exam_entry_reviewed_by ON exam_entry(reviewed_by) WHERE reviewed_by IS NOT NULL;

-- EXAM_CLASS indexes
CREATE INDEX IX_exam_class_exam_id ON exam_class(exam_id);
CREATE INDEX IX_exam_class_course_class_id ON exam_class(course_class_id);
CREATE INDEX IX_exam_class_room_id ON exam_class(room_id);
CREATE INDEX IX_exam_class_monitor_instructor_id ON exam_class(monitor_instructor_id) WHERE monitor_instructor_id IS NOT NULL;
CREATE INDEX IX_exam_class_start_time ON exam_class(start_time);
CREATE INDEX IX_exam_class_exam_status ON exam_class(exam_status);

-- STUDENT_HEALTH_INSURANCE indexes
CREATE INDEX IX_student_health_insurance_student_id ON student_health_insurance(student_id);
CREATE INDEX IX_student_health_insurance_academic_year_id ON student_health_insurance(academic_year_id);
CREATE INDEX IX_student_health_insurance_dates ON student_health_insurance(start_date, end_date);
CREATE INDEX IX_student_health_insurance_insurance_status ON student_health_insurance(insurance_status);

-- PAYMENT_ENROLLMENT indexes
CREATE INDEX IX_payment_enrollment_student_id ON payment_enrollment(student_id);
CREATE INDEX IX_payment_enrollment_semester_id ON payment_enrollment(semester_id);
CREATE INDEX IX_payment_enrollment_payment_date ON payment_enrollment(payment_date);
CREATE INDEX IX_payment_enrollment_payment_status ON payment_enrollment(payment_status);

-- PAYMENT_ENROLLMENT_DETAIL indexes
CREATE INDEX IX_payment_enrollment_detail_payment_id ON payment_enrollment_detail(payment_id);
CREATE INDEX IX_payment_enrollment_detail_enrollment_id ON payment_enrollment_detail(enrollment_id);

-- PAYMENT_INSURANCE indexes
CREATE INDEX IX_payment_insurance_insurance_id ON payment_insurance(insurance_id);
CREATE INDEX IX_payment_insurance_payment_date ON payment_insurance(payment_date);
CREATE INDEX IX_payment_insurance_payment_status ON payment_insurance(payment_status);

-- ROOM_BOOKING indexes
CREATE INDEX IX_room_booking_room_id ON room_booking(room_id);
CREATE INDEX IX_room_booking_booked_by ON room_booking(booked_by);
CREATE INDEX IX_room_booking_booking_date ON room_booking(booking_date);
CREATE INDEX IX_room_booking_booking_status ON room_booking(booking_status);
CREATE INDEX IX_room_booking_room_date ON room_booking(room_id, booking_date);

-- REGULATION indexes
CREATE INDEX IX_regulation_target ON regulation(target);
CREATE INDEX IX_regulation_created_by_admin ON regulation(created_by_admin);
CREATE INDEX IX_regulation_expire_date ON regulation(expire_date) WHERE expire_date IS NOT NULL;

-- STUDENT_VERIFICATION_REQUEST indexes
CREATE INDEX IX_student_verification_request_student_id ON student_verification_request(student_id);
CREATE INDEX IX_student_verification_request_request_status ON student_verification_request(request_status);
CREATE INDEX IX_student_verification_request_created_at ON student_verification_request(created_at DESC);

-- PAYMENT_POSTPONEMENT_REQUEST indexes
CREATE INDEX IX_payment_postponement_request_student_id ON payment_postponement_request(student_id);
CREATE INDEX IX_payment_postponement_request_semester_id ON payment_postponement_request(semester_id);
CREATE INDEX IX_payment_postponement_request_request_status ON payment_postponement_request(request_status);
CREATE INDEX IX_payment_postponement_request_reviewed_by ON payment_postponement_request(reviewed_by) WHERE reviewed_by IS NOT NULL;

-- NOTE indexes
CREATE INDEX IX_note_student_id ON note(student_id);
CREATE INDEX IX_note_created_at ON note(created_at DESC);

-- SCHEDULE_CHANGE_REQUEST indexes
CREATE INDEX IX_schedule_change_request_course_class_id ON schedule_change_request(course_class_id);
CREATE INDEX IX_schedule_change_request_makeup_room_id ON schedule_change_request(makeup_room_id) WHERE makeup_room_id IS NOT NULL;
CREATE INDEX IX_schedule_change_request_status ON schedule_change_request(status);
CREATE INDEX IX_schedule_change_request_created_by ON schedule_change_request(created_by) WHERE created_by IS NOT NULL;
CREATE INDEX IX_schedule_change_request_reviewed_by ON schedule_change_request(reviewed_by) WHERE reviewed_by IS NOT NULL;

-- CHAT_HISTORY indexes (already defined in table creation, including these for completeness)
-- IX_chat_history_user_session already exists
-- IX_chat_history_session already exists

-- KNOWLEDGE_DOCUMENTS indexes (already defined in table creation, including these for completeness)
-- IX_knowledge_role_type already exists
-- IX_knowledge_doc_type already exists
-- IX_knowledge_created already exists

-- Composite indexes for common query patterns
CREATE INDEX IX_course_class_schedule ON course_class(date_start, date_end, day_of_week, start_period, end_period);
CREATE INDEX IX_student_enrollment_active ON student_enrollment(student_id, enrollment_status) WHERE enrollment_status = 'registered';
CREATE INDEX IX_notification_schedule_pending ON notification_schedule(visible_from, status) WHERE status = 'pending';
CREATE INDEX IX_exam_entry_pending_approval ON exam_entry(exam_id, entry_status) WHERE entry_status = 'pending';

GO