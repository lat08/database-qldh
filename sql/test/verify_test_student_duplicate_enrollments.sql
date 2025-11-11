USE EduManagement;
GO

-- ============================================================
-- VERIFY TEST STUDENT DUPLICATE ENROLLMENTS
-- ============================================================
-- This query identifies test students who have multiple enrollments 
-- for the same subject across different courses/semesters

-- ============================================================
-- 1. TEST STUDENTS WITH DUPLICATE SUBJECT ENROLLMENTS
-- ============================================================
-- Shows test students enrolled in multiple courses of the same subject
SELECT 
    s.student_id,
    s.student_code,
    p.full_name AS student_name,
    subj.subject_id,
    subj.subject_code,
    subj.subject_name,
    COUNT(DISTINCT se.course_class_id) AS enrollment_count,
    STRING_AGG(
        CONCAT(
            c.course_id, ' (', 
            sem.semester_name, ' - ', 
            cc.date_start, ' to ', cc.date_end, ')'
        ), 
        '; '
    ) AS enrolled_courses
FROM 
    student s
    INNER JOIN person p ON s.person_id = p.person_id
    INNER JOIN student_enrollment se ON s.student_id = se.student_id
    INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
    INNER JOIN course c ON cc.course_id = c.course_id
    INNER JOIN subject subj ON c.subject_id = subj.subject_id
    INNER JOIN semester sem ON c.semester_id = sem.semester_id
WHERE 
    -- Filter for test students based on specific student codes
    s.student_code IN ('SV999999', 'SV001', 'SV007', 'SV008')
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed')
    AND cc.is_deleted = 0
    AND cc.is_active = 1
GROUP BY 
    s.student_id,
    s.student_code,
    p.full_name,
    subj.subject_id,
    subj.subject_code,
    subj.subject_name
HAVING 
    COUNT(DISTINCT se.course_class_id) > 1  -- More than 1 enrollment for same subject
ORDER BY 
    s.student_code, 
    subj.subject_code;

-- ============================================================
-- 2. DETAILED VIEW OF DUPLICATE ENROLLMENTS
-- ============================================================
-- Shows detailed information about each duplicate enrollment
SELECT 
    'DUPLICATE_ENROLLMENT_DETAIL' AS report_type,
    s.student_code,
    p.full_name AS student_name,
    subj.subject_code,
    subj.subject_name,
    c.course_id,
    sem.semester_name,
    cc.course_class_id,
    cc.date_start,
    cc.date_end,
    se.enrollment_date,
    se.enrollment_status,
    r.room_code,
    cc.day_of_week,
    cc.start_period,
    cc.end_period,
    i.instructor_code,
    p_inst.full_name AS instructor_name
FROM 
    student s
    INNER JOIN person p ON s.person_id = p.person_id
    INNER JOIN student_enrollment se ON s.student_id = se.student_id
    INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
    INNER JOIN course c ON cc.course_id = c.course_id
    INNER JOIN subject subj ON c.subject_id = subj.subject_id
    INNER JOIN semester sem ON c.semester_id = sem.semester_id
    LEFT JOIN room r ON cc.room_id = r.room_id
    LEFT JOIN instructor i ON cc.instructor_id = i.instructor_id
    LEFT JOIN person p_inst ON i.person_id = p_inst.person_id
WHERE 
    s.student_code IN ('SV999999', 'SV001', 'SV007', 'SV008')
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed')
    AND cc.is_deleted = 0
    AND cc.is_active = 1
    -- Only show subjects where the test student has multiple enrollments
    AND subj.subject_id IN (
        SELECT 
            subj2.subject_id
        FROM 
            student s2
            INNER JOIN student_enrollment se2 ON s2.student_id = se2.student_id
            INNER JOIN course_class cc2 ON se2.course_class_id = cc2.course_class_id
            INNER JOIN course c2 ON cc2.course_id = c2.course_id
            INNER JOIN subject subj2 ON c2.subject_id = subj2.subject_id
        WHERE 
            s2.student_id = s.student_id
            AND se2.is_deleted = 0
            AND se2.is_active = 1
            AND se2.enrollment_status IN ('registered', 'completed')
            AND cc2.is_deleted = 0
            AND cc2.is_active = 1
        GROUP BY 
            subj2.subject_id
        HAVING 
            COUNT(DISTINCT se2.course_class_id) > 1
    )
ORDER BY 
    s.student_code, 
    subj.subject_code,
    sem.semester_name,
    cc.date_start;

-- ============================================================
-- 3. SUMMARY COUNT OF DUPLICATE ENROLLMENTS
-- ============================================================
-- Summary statistics for test student duplicate enrollments
SELECT 
    'SUMMARY' AS report_type,
    COUNT(DISTINCT s.student_id) AS test_students_with_duplicates,
    COUNT(DISTINCT subj.subject_id) AS subjects_with_duplicates,
    SUM(duplicate_count - 1) AS total_excess_enrollments
FROM (
    SELECT 
        s.student_id,
        subj.subject_id,
        COUNT(DISTINCT se.course_class_id) AS duplicate_count
    FROM 
        student s
        INNER JOIN student_enrollment se ON s.student_id = se.student_id
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject subj ON c.subject_id = subj.subject_id
    WHERE 
        s.student_code IN ('SV999999', 'SV001', 'SV007', 'SV008')
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
        AND cc.is_deleted = 0
        AND cc.is_active = 1
    GROUP BY 
        s.student_id,
        subj.subject_id
    HAVING 
        COUNT(DISTINCT se.course_class_id) > 1
) AS duplicates
CROSS JOIN (
    SELECT 
        subj.subject_id,
        s.student_id
    FROM 
        student s
        INNER JOIN student_enrollment se ON s.student_id = se.student_id
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject subj ON c.subject_id = subj.subject_id
    WHERE 
        s.student_code IN ('SV999999', 'SV001', 'SV007', 'SV008')
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
        AND cc.is_deleted = 0
        AND cc.is_active = 1
    GROUP BY 
        s.student_id,
        subj.subject_id
    HAVING 
        COUNT(DISTINCT se.course_class_id) > 1
) AS s
CROSS JOIN (
    SELECT 
        subj.subject_id
    FROM 
        student s
        INNER JOIN student_enrollment se ON s.student_id = se.student_id
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject subj ON c.subject_id = subj.subject_id
    WHERE 
        s.student_code IN ('SV999999', 'SV001', 'SV007', 'SV008')
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
        AND cc.is_deleted = 0
        AND cc.is_active = 1
    GROUP BY 
        subj.subject_id
    HAVING 
        COUNT(DISTINCT CASE WHEN s.student_code IN ('SV999999', 'SV001', 'SV007', 'SV008') THEN se.course_class_id END) > 
        COUNT(DISTINCT CASE WHEN s.student_code IN ('SV999999', 'SV001', 'SV007', 'SV008') THEN s.student_id END)
) AS subj;

-- ============================================================
-- 4. ALTERNATIVE SIMPLIFIED SUMMARY
-- ============================================================
-- Simplified summary of duplicate enrollments per test student
SELECT 
    'STUDENT_SUMMARY' AS report_type,
    s.student_code,
    p.full_name AS student_name,
    COUNT(DISTINCT subj.subject_id) AS total_subjects_enrolled,
    COUNT(DISTINCT se.course_class_id) AS total_course_enrollments,
    COUNT(DISTINCT se.course_class_id) - COUNT(DISTINCT subj.subject_id) AS excess_enrollments,
    CASE 
        WHEN COUNT(DISTINCT se.course_class_id) > COUNT(DISTINCT subj.subject_id) 
        THEN 'HAS DUPLICATES'
        ELSE 'NO DUPLICATES'
    END AS duplicate_status
FROM 
    student s
    INNER JOIN person p ON s.person_id = p.person_id
    INNER JOIN student_enrollment se ON s.student_id = se.student_id
    INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
    INNER JOIN course c ON cc.course_id = c.course_id
    INNER JOIN subject subj ON c.subject_id = subj.subject_id
WHERE 
    s.student_code IN ('SV999999', 'SV001', 'SV007', 'SV008')
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed')
    AND cc.is_deleted = 0
    AND cc.is_active = 1
GROUP BY 
    s.student_id,
    s.student_code,
    p.full_name
ORDER BY 
    excess_enrollments DESC,
    s.student_code;

-- ============================================================
-- 5. TEST STUDENT TOTAL ENROLLMENT OVERVIEW
-- ============================================================
-- Overview of all test student enrollments for context
SELECT 
    'ENROLLMENT_OVERVIEW' AS report_type,
    s.student_code,
    p.full_name AS student_name,
    COUNT(*) AS total_enrollments,
    COUNT(DISTINCT subj.subject_id) AS unique_subjects,
    COUNT(DISTINCT sem.semester_id) AS semesters_enrolled,
    MIN(cc.date_start) AS earliest_course,
    MAX(cc.date_end) AS latest_course
FROM 
    student s
    INNER JOIN person p ON s.person_id = p.person_id
    INNER JOIN student_enrollment se ON s.student_id = se.student_id
    INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
    INNER JOIN course c ON cc.course_id = c.course_id
    INNER JOIN subject subj ON c.subject_id = subj.subject_id
    INNER JOIN semester sem ON c.semester_id = sem.semester_id
WHERE 
    s.student_code IN ('SV999999', 'SV001', 'SV007', 'SV008')
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed')
    AND cc.is_deleted = 0
    AND cc.is_active = 1
GROUP BY 
    s.student_id,
    s.student_code,
    p.full_name
ORDER BY 
    s.student_code;

GO