USE EduManagement;
GO

-- ============================================================
-- 1. COUNT COURSE CLASSES WITH 0 ENROLLMENTS
-- ============================================================
-- Counts course classes that have no active student enrollments
SELECT 
    COUNT(*) AS course_classes_with_zero_enrollments
FROM 
    course_class cc
WHERE 
    cc.is_deleted = 0 
    AND cc.is_active = 1
    AND NOT EXISTS (
        SELECT 1 
        FROM student_enrollment se
        WHERE se.course_class_id = cc.course_class_id
            AND se.is_deleted = 0
            AND se.is_active = 1
            AND se.enrollment_status IN ('registered', 'completed')
    );

-- Alternative: Detailed view showing which course classes have 0 enrollments
SELECT 
    cc.course_class_id,
    cc.course_id,
    c.subject_id,
    s.subject_name,
    s.subject_code,
    cc.instructor_id,
    i.instructor_code,
    cc.room_id,
    r.room_code,
    cc.day_of_week,
    cc.start_period,
    cc.end_period,
    cc.date_start,
    cc.date_end,
    cc.course_class_status,
    COUNT(se.enrollment_id) AS enrollment_count
FROM 
    course_class cc
    INNER JOIN course c ON cc.course_id = c.course_id
    INNER JOIN subject s ON c.subject_id = s.subject_id
    LEFT JOIN instructor i ON cc.instructor_id = i.instructor_id
    LEFT JOIN room r ON cc.room_id = r.room_id
    LEFT JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
WHERE 
    cc.is_deleted = 0 
    AND cc.is_active = 1
GROUP BY 
    cc.course_class_id,
    cc.course_id,
    c.subject_id,
    s.subject_name,
    s.subject_code,
    cc.instructor_id,
    i.instructor_code,
    cc.room_id,
    r.room_code,
    cc.day_of_week,
    cc.start_period,
    cc.end_period,
    cc.date_start,
    cc.date_end,
    cc.course_class_status
HAVING 
    COUNT(se.enrollment_id) = 0;

-- ============================================================
-- 2. COURSES WITH SCHEDULE CONFLICTS
-- ============================================================
-- Finds course classes that have room conflicts (same room, same day, overlapping time and dates)
SELECT 
    cc1.course_class_id AS course_class_1_id,
    s1.subject_name AS course_class_1_subject,
    s1.subject_code AS course_class_1_code,
    r1.room_code AS room_code,
    cc1.day_of_week,
    cc1.start_period AS class1_start_period,
    cc1.end_period AS class1_end_period,
    cc1.date_start AS class1_date_start,
    cc1.date_end AS class1_date_end,
    
    cc2.course_class_id AS course_class_2_id,
    s2.subject_name AS course_class_2_subject,
    s2.subject_code AS course_class_2_code,
    cc2.start_period AS class2_start_period,
    cc2.end_period AS class2_end_period,
    cc2.date_start AS class2_date_start,
    cc2.date_end AS class2_date_end,
    
    CASE 
        WHEN cc1.course_class_id < cc2.course_class_id THEN 'Conflict'
        ELSE 'Duplicate'
    END AS conflict_type
FROM 
    course_class cc1
    INNER JOIN course c1 ON cc1.course_id = c1.course_id
    INNER JOIN subject s1 ON c1.subject_id = s1.subject_id
    INNER JOIN room r1 ON cc1.room_id = r1.room_id
    
    INNER JOIN course_class cc2 ON 
        cc1.room_id = cc2.room_id  -- Same room
        AND cc1.day_of_week = cc2.day_of_week  -- Same day of week
        AND cc1.course_class_id < cc2.course_class_id  -- Avoid duplicates and self-joins
        AND (
            -- Date ranges overlap
            (cc1.date_start <= cc2.date_end AND cc1.date_end >= cc2.date_start)
        )
        AND (
            -- Time periods overlap
            (cc1.start_period <= cc2.end_period AND cc1.end_period >= cc2.start_period)
        )
    
    INNER JOIN course c2 ON cc2.course_id = c2.course_id
    INNER JOIN subject s2 ON c2.subject_id = s2.subject_id
WHERE 
    cc1.is_deleted = 0 
    AND cc1.is_active = 1
    AND cc1.course_class_status IN ('active', 'pending')
    AND cc2.is_deleted = 0 
    AND cc2.is_active = 1
    AND cc2.course_class_status IN ('active', 'pending')
ORDER BY 
    r1.room_code, cc1.day_of_week, cc1.start_period;

-- Summary count of conflicting course classes
SELECT 
    COUNT(DISTINCT CASE WHEN cc1.course_class_id < cc2.course_class_id THEN cc1.course_class_id ELSE cc2.course_class_id END) 
        + COUNT(DISTINCT CASE WHEN cc1.course_class_id < cc2.course_class_id THEN cc2.course_class_id ELSE NULL END) 
    AS total_conflicting_course_classes
FROM 
    course_class cc1
    INNER JOIN course_class cc2 ON 
        cc1.room_id = cc2.room_id
        AND cc1.day_of_week = cc2.day_of_week
        AND cc1.course_class_id < cc2.course_class_id
        AND (cc1.date_start <= cc2.date_end AND cc1.date_end >= cc2.date_start)
        AND (cc1.start_period <= cc2.end_period AND cc1.end_period >= cc2.start_period)
WHERE 
    cc1.is_deleted = 0 
    AND cc1.is_active = 1
    AND cc1.course_class_status IN ('active', 'pending')
    AND cc2.is_deleted = 0 
    AND cc2.is_active = 1
    AND cc2.course_class_status IN ('active', 'pending');

-- ============================================================
-- 3. INSTRUCTOR COURSES WITH INSTRUCTOR SCHEDULE CONFLICTS
-- ============================================================
-- Finds course classes where the same instructor is scheduled to teach
-- multiple classes at the same time (same day, overlapping periods and dates)
SELECT 
    cc1.course_class_id AS course_class_1_id,
    s1.subject_name AS course_class_1_subject,
    s1.subject_code AS course_class_1_code,
    i.instructor_code,
    p1.full_name AS instructor_name,
    r1.room_code AS class1_room,
    cc1.day_of_week,
    cc1.start_period AS class1_start_period,
    cc1.end_period AS class1_end_period,
    cc1.date_start AS class1_date_start,
    cc1.date_end AS class1_date_end,
    
    cc2.course_class_id AS course_class_2_id,
    s2.subject_name AS course_class_2_subject,
    s2.subject_code AS course_class_2_code,
    r2.room_code AS class2_room,
    cc2.start_period AS class2_start_period,
    cc2.end_period AS class2_end_period,
    cc2.date_start AS class2_date_start,
    cc2.date_end AS class2_date_end
FROM 
    course_class cc1
    INNER JOIN course c1 ON cc1.course_id = c1.course_id
    INNER JOIN subject s1 ON c1.subject_id = s1.subject_id
    INNER JOIN instructor i ON cc1.instructor_id = i.instructor_id
    INNER JOIN person p1 ON i.person_id = p1.person_id
    INNER JOIN room r1 ON cc1.room_id = r1.room_id
    
    INNER JOIN course_class cc2 ON 
        cc1.instructor_id = cc2.instructor_id  -- Same instructor
        AND cc1.instructor_id IS NOT NULL  -- Ensure instructor is assigned
        AND cc1.day_of_week = cc2.day_of_week  -- Same day of week
        AND cc1.course_class_id < cc2.course_class_id  -- Avoid duplicates and self-joins
        AND (
            -- Date ranges overlap
            (cc1.date_start <= cc2.date_end AND cc1.date_end >= cc2.date_start)
        )
        AND (
            -- Time periods overlap
            (cc1.start_period <= cc2.end_period AND cc1.end_period >= cc2.start_period)
        )
    
    INNER JOIN course c2 ON cc2.course_id = c2.course_id
    INNER JOIN subject s2 ON c2.subject_id = s2.subject_id
    INNER JOIN room r2 ON cc2.room_id = r2.room_id
WHERE 
    cc1.is_deleted = 0 
    AND cc1.is_active = 1
    AND cc1.course_class_status IN ('active', 'pending')
    AND cc2.is_deleted = 0 
    AND cc2.is_active = 1
    AND cc2.course_class_status IN ('active', 'pending')
ORDER BY 
    i.instructor_code, cc1.day_of_week, cc1.start_period;

-- Summary count of instructors with schedule conflicts
SELECT 
    COUNT(DISTINCT cc1.instructor_id) AS instructors_with_conflicts,
    COUNT(DISTINCT CASE WHEN cc1.course_class_id < cc2.course_class_id THEN cc1.course_class_id ELSE cc2.course_class_id END) 
        + COUNT(DISTINCT CASE WHEN cc1.course_class_id < cc2.course_class_id THEN cc2.course_class_id ELSE NULL END) 
    AS total_conflicting_course_classes
FROM 
    course_class cc1
    INNER JOIN course_class cc2 ON 
        cc1.instructor_id = cc2.instructor_id
        AND cc1.instructor_id IS NOT NULL
        AND cc1.day_of_week = cc2.day_of_week
        AND cc1.course_class_id < cc2.course_class_id
        AND (cc1.date_start <= cc2.date_end AND cc1.date_end >= cc2.date_start)
        AND (cc1.start_period <= cc2.end_period AND cc1.end_period >= cc2.start_period)
WHERE 
    cc1.is_deleted = 0 
    AND cc1.is_active = 1
    AND cc1.course_class_status IN ('active', 'pending')
    AND cc2.is_deleted = 0 
    AND cc2.is_active = 1
    AND cc2.course_class_status IN ('active', 'pending');

