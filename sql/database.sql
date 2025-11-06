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

-- ============================================================
-- FACULTY
-- ============================================================
CREATE TABLE faculty (
    faculty_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    faculty_name NVARCHAR(200) NOT NULL,
    faculty_code NVARCHAR(50) NOT NULL UNIQUE,
    dean_id UNIQUEIDENTIFIER NULL,
    faculty_status NVARCHAR(20) DEFAULT 'active' CHECK (faculty_status IN ('active','inactive')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
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
ALTER TABLE faculty 
    ADD CONSTRAINT FK_faculty_dean_instructor 
    FOREIGN KEY (dean_id) REFERENCES instructor(instructor_id) ON DELETE SET NULL;

-- ============================================================
-- SUBJECT
-- ============================================================
CREATE TABLE subject (
    subject_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    subject_name NVARCHAR(200) NOT NULL,
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
        REFERENCES semester(semester_id) ON DELETE CASCADE
);

-- ============================================================
-- COURSE CLASS
-- ============================================================
CREATE TABLE course_class (
    course_class_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_id UNIQUEIDENTIFIER NOT NULL,
    instructor_id UNIQUEIDENTIFIER NULL,
    room_id UNIQUEIDENTIFIER NOT NULL,
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

    CONSTRAINT CHK_course_class_dates CHECK (date_end > date_start)
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
    scheduled_date DATETIME2 NOT NULL,
    visible_from DATETIME2 NOT NULL,
    is_read BIT NOT NULL DEFAULT 0,
    target_type NVARCHAR(50) NOT NULL CHECK (target_type IN ('all', 'all_students', 'all_instructors', 'class', 'faculty', 'instructor')),
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
