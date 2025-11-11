-- ============================================================
-- VERIFY SUMMER 2024-2025 GRADES COVERAGE
-- ============================================================
-- This query verifies that ALL summer 2024-2025 enrollments have:
-- - Draft grades (attendance and midterm) OR
-- - Official grades (attendance and midterm) in grade versions
-- This ensures complete grade coverage for the current semester

USE EduManagement;
GO

DECLARE @TODAY DATE = CAST(GETDATE() AS DATE);

-- Find summer 2024-2025 semester
DECLARE @SummerSemesterId UNIQUEIDENTIFIER;
SELECT @SummerSemesterId = s.semester_id
FROM semester s
INNER JOIN academic_year ay ON s.academic_year_id = ay.academic_year_id
WHERE s.semester_type = 'summer'
    AND ay.year_name = '2024-2025'  -- Academic year 2024-2025
    AND MONTH(s.end_date) = 11      -- Ends in November
    AND YEAR(s.end_date) = 2025;    -- Year 2025

-- Display semester info
SELECT 
    'SEMESTER INFO' AS section,
    s.semester_name,
    s.start_date,
    s.end_date,
    s.semester_status,
    COUNT(cc.course_class_id) AS total_course_classes
FROM semester s
LEFT JOIN course c ON s.semester_id = c.semester_id
LEFT JOIN course_class cc ON c.course_id = cc.course_id
WHERE s.semester_id = @SummerSemesterId
GROUP BY s.semester_name, s.start_date, s.end_date, s.semester_status;

-- ============================================================
-- 1. TOTAL ENROLLMENTS IN SUMMER 2024-2025
-- ============================================================
SELECT 
    'ENROLLMENT SUMMARY' AS section,
    COUNT(*) AS total_enrollments,
    COUNT(DISTINCT se.student_id) AS unique_students,
    COUNT(DISTINCT se.course_class_id) AS unique_course_classes
FROM student_enrollment se
INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
WHERE c.semester_id = @SummerSemesterId
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed');

-- ============================================================
-- 2. DRAFT GRADES COVERAGE
-- ============================================================
SELECT 
    'DRAFT GRADES SUMMARY' AS section,
    COUNT(se.enrollment_id) AS total_enrollments,
    COUNT(edg.draft_grade_id) AS enrollments_with_draft_grades,
    COUNT(CASE WHEN edg.attendance_grade_draft IS NOT NULL THEN 1 END) AS with_attendance_draft,
    COUNT(CASE WHEN edg.midterm_grade_draft IS NOT NULL THEN 1 END) AS with_midterm_draft,
    COUNT(CASE WHEN edg.final_grade_draft IS NOT NULL THEN 1 END) AS with_final_draft,
    COUNT(CASE 
        WHEN edg.attendance_grade_draft IS NOT NULL 
        AND edg.midterm_grade_draft IS NOT NULL THEN 1 
    END) AS with_both_attendance_and_midterm,
    ROUND(
        CAST(COUNT(edg.draft_grade_id) AS FLOAT) / 
        CAST(COUNT(se.enrollment_id) AS FLOAT) * 100, 2
    ) AS draft_grade_coverage_percentage
FROM student_enrollment se
INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
LEFT JOIN enrollment_draft_grade edg ON se.enrollment_id = edg.enrollment_id
WHERE c.semester_id = @SummerSemesterId
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed');

-- ============================================================
-- 3. OFFICIAL GRADES COVERAGE (GRADE VERSIONS)
-- ============================================================
SELECT 
    'OFFICIAL GRADES SUMMARY' AS section,
    COUNT(se.enrollment_id) AS total_enrollments,
    COUNT(egd.grade_detail_id) AS enrollments_with_official_grades,
    COUNT(CASE WHEN egd.attendance_grade IS NOT NULL THEN 1 END) AS with_attendance_official,
    COUNT(CASE WHEN egd.midterm_grade IS NOT NULL THEN 1 END) AS with_midterm_official,
    COUNT(CASE WHEN egd.final_grade IS NOT NULL THEN 1 END) AS with_final_official,
    COUNT(CASE 
        WHEN egd.attendance_grade IS NOT NULL 
        AND egd.midterm_grade IS NOT NULL THEN 1 
    END) AS with_both_attendance_and_midterm_official,
    ROUND(
        CAST(COUNT(egd.grade_detail_id) AS FLOAT) / 
        CAST(COUNT(se.enrollment_id) AS FLOAT) * 100, 2
    ) AS official_grade_coverage_percentage
FROM student_enrollment se
INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
LEFT JOIN enrollment_grade_version egv ON cc.course_class_id = egv.course_class_id
LEFT JOIN enrollment_grade_detail egd ON egv.grade_version_id = egd.grade_version_id 
    AND se.enrollment_id = egd.enrollment_id
WHERE c.semester_id = @SummerSemesterId
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed');

-- ============================================================
-- 4. COMBINED COVERAGE (EITHER DRAFT OR OFFICIAL)
-- ============================================================
SELECT 
    'COMBINED COVERAGE' AS section,
    COUNT(se.enrollment_id) AS total_enrollments,
    COUNT(CASE 
        WHEN edg.draft_grade_id IS NOT NULL OR egd.grade_detail_id IS NOT NULL 
        THEN 1 
    END) AS enrollments_with_any_grades,
    COUNT(CASE 
        WHEN (edg.attendance_grade_draft IS NOT NULL OR egd.attendance_grade IS NOT NULL)
        AND (edg.midterm_grade_draft IS NOT NULL OR egd.midterm_grade IS NOT NULL)
        THEN 1 
    END) AS with_attendance_and_midterm_any,
    ROUND(
        CAST(COUNT(CASE 
            WHEN (edg.attendance_grade_draft IS NOT NULL OR egd.attendance_grade IS NOT NULL)
            AND (edg.midterm_grade_draft IS NOT NULL OR egd.midterm_grade IS NOT NULL)
            THEN 1 
        END) AS FLOAT) / 
        CAST(COUNT(se.enrollment_id) AS FLOAT) * 100, 2
    ) AS complete_grade_coverage_percentage
FROM student_enrollment se
INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
LEFT JOIN enrollment_draft_grade edg ON se.enrollment_id = edg.enrollment_id
LEFT JOIN enrollment_grade_version egv ON cc.course_class_id = egv.course_class_id
LEFT JOIN enrollment_grade_detail egd ON egv.grade_version_id = egd.grade_version_id 
    AND se.enrollment_id = egd.enrollment_id
WHERE c.semester_id = @SummerSemesterId
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed');

-- ============================================================
-- 5. ENROLLMENTS WITHOUT COMPLETE GRADES (ISSUES)
-- ============================================================
SELECT 
    'ENROLLMENTS WITHOUT COMPLETE GRADES' AS section,
    p.full_name AS student_name,
    p.email AS student_email,
    s.subject_code,
    s.subject_name,
    se.enrollment_status,
    CASE 
        WHEN edg.attendance_grade_draft IS NOT NULL OR egd.attendance_grade IS NOT NULL 
        THEN 'YES' ELSE 'NO' 
    END AS has_attendance_grade,
    CASE 
        WHEN edg.midterm_grade_draft IS NOT NULL OR egd.midterm_grade IS NOT NULL 
        THEN 'YES' ELSE 'NO' 
    END AS has_midterm_grade,
    CASE 
        WHEN edg.final_grade_draft IS NOT NULL OR egd.final_grade IS NOT NULL 
        THEN 'YES' ELSE 'NO' 
    END AS has_final_grade,
    cc.grade_submission_status
FROM student_enrollment se
INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
INNER JOIN subject s ON c.subject_id = s.subject_id
INNER JOIN student st ON se.student_id = st.student_id
INNER JOIN person p ON st.person_id = p.person_id
LEFT JOIN enrollment_draft_grade edg ON se.enrollment_id = edg.enrollment_id
LEFT JOIN enrollment_grade_version egv ON cc.course_class_id = egv.course_class_id
LEFT JOIN enrollment_grade_detail egd ON egv.grade_version_id = egd.grade_version_id 
    AND se.enrollment_id = egd.enrollment_id
WHERE c.semester_id = @SummerSemesterId
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed')
    AND NOT (
        (edg.attendance_grade_draft IS NOT NULL OR egd.attendance_grade IS NOT NULL)
        AND (edg.midterm_grade_draft IS NOT NULL OR egd.midterm_grade IS NOT NULL)
    )
ORDER BY p.full_name, s.subject_code;

-- ============================================================
-- 6. GRADE DISTRIBUTION ANALYSIS
-- ============================================================
SELECT 
    'GRADE DISTRIBUTION ANALYSIS' AS section,
    'Attendance Grades' AS grade_type,
    COUNT(CASE WHEN attendance_grade BETWEEN 7.0 AND 7.9 THEN 1 END) AS grade_7_to_7_9,
    COUNT(CASE WHEN attendance_grade BETWEEN 8.0 AND 8.9 THEN 1 END) AS grade_8_to_8_9,
    COUNT(CASE WHEN attendance_grade BETWEEN 9.0 AND 10.0 THEN 1 END) AS grade_9_to_10,
    ROUND(AVG(attendance_grade), 2) AS average_attendance_grade
FROM (
    SELECT 
        COALESCE(edg.attendance_grade_draft, egd.attendance_grade) AS attendance_grade
    FROM student_enrollment se
    INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
    INNER JOIN course c ON cc.course_id = c.course_id
    LEFT JOIN enrollment_draft_grade edg ON se.enrollment_id = edg.enrollment_id
    LEFT JOIN enrollment_grade_version egv ON cc.course_class_id = egv.course_class_id
    LEFT JOIN enrollment_grade_detail egd ON egv.grade_version_id = egd.grade_version_id 
        AND se.enrollment_id = egd.enrollment_id
    WHERE c.semester_id = @SummerSemesterId
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
        AND (edg.attendance_grade_draft IS NOT NULL OR egd.attendance_grade IS NOT NULL)
) AS attendance_grades

UNION ALL

SELECT 
    'GRADE DISTRIBUTION ANALYSIS' AS section,
    'Midterm Grades' AS grade_type,
    COUNT(CASE WHEN midterm_grade BETWEEN 5.0 AND 6.9 THEN 1 END) AS grade_5_to_6_9,
    COUNT(CASE WHEN midterm_grade BETWEEN 7.0 AND 8.9 THEN 1 END) AS grade_7_to_8_9,
    COUNT(CASE WHEN midterm_grade BETWEEN 9.0 AND 9.5 THEN 1 END) AS grade_9_to_9_5,
    ROUND(AVG(midterm_grade), 2) AS average_midterm_grade
FROM (
    SELECT 
        COALESCE(edg.midterm_grade_draft, egd.midterm_grade) AS midterm_grade
    FROM student_enrollment se
    INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
    INNER JOIN course c ON cc.course_id = c.course_id
    LEFT JOIN enrollment_draft_grade edg ON se.enrollment_id = edg.enrollment_id
    LEFT JOIN enrollment_grade_version egv ON cc.course_class_id = egv.course_class_id
    LEFT JOIN enrollment_grade_detail egd ON egv.grade_version_id = egd.grade_version_id 
        AND se.enrollment_id = egd.enrollment_id
    WHERE c.semester_id = @SummerSemesterId
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
        AND (edg.midterm_grade_draft IS NOT NULL OR egd.midterm_grade IS NOT NULL)
) AS midterm_grades;

-- ============================================================
-- 7. GRADE SUBMISSION STATUS BY COURSE CLASS
-- ============================================================
SELECT 
    'GRADE SUBMISSION STATUS' AS section,
    s.subject_code,
    s.subject_name,
    LEFT(cc.course_class_id, 8) + '...' AS course_class_short_id,
    cc.grade_submission_status,
    COUNT(se.enrollment_id) AS total_enrollments,
    COUNT(edg.draft_grade_id) AS draft_grades_count,
    COUNT(egd.grade_detail_id) AS official_grades_count,
    CASE 
        WHEN cc.grade_submission_status = 'draft' THEN 'Instructor still working on grades'
        WHEN cc.grade_submission_status = 'pending' THEN 'Submitted for approval'
        WHEN cc.grade_submission_status = 'approved' THEN 'Grades finalized'
        ELSE 'Unknown status'
    END AS status_description
FROM course_class cc
INNER JOIN course c ON cc.course_id = c.course_id
INNER JOIN subject s ON c.subject_id = s.subject_id
LEFT JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
    AND se.is_deleted = 0 AND se.is_active = 1 
    AND se.enrollment_status IN ('registered', 'completed')
LEFT JOIN enrollment_draft_grade edg ON se.enrollment_id = edg.enrollment_id
LEFT JOIN enrollment_grade_version egv ON cc.course_class_id = egv.course_class_id
LEFT JOIN enrollment_grade_detail egd ON egv.grade_version_id = egd.grade_version_id 
    AND se.enrollment_id = egd.enrollment_id
WHERE c.semester_id = @SummerSemesterId
    AND cc.is_deleted = 0
    AND cc.is_active = 1
GROUP BY s.subject_code, s.subject_name, cc.course_class_id, cc.grade_submission_status
ORDER BY s.subject_code, cc.course_class_id;

-- ============================================================
-- SUCCESS CRITERIA CHECK
-- ============================================================
-- This should show 100% coverage for attendance and midterm grades
SELECT 
    'SUCCESS CRITERIA' AS section,
    CASE 
        WHEN coverage_percentage = 100 
        THEN '✓ PASS: All enrollments have complete grades'
        WHEN coverage_percentage >= 95 
        THEN '⚠ WARNING: Most enrollments have grades (' + CAST(coverage_percentage AS VARCHAR(10)) + '%)'
        ELSE '✗ FAIL: Many enrollments missing grades (' + CAST(coverage_percentage AS VARCHAR(10)) + '%)'
    END AS result,
    coverage_percentage AS percentage
FROM (
    SELECT 
        ROUND(
            CAST(COUNT(CASE 
                WHEN (edg.attendance_grade_draft IS NOT NULL OR egd.attendance_grade IS NOT NULL)
                AND (edg.midterm_grade_draft IS NOT NULL OR egd.midterm_grade IS NOT NULL)
                THEN 1 
            END) AS FLOAT) / 
            CAST(COUNT(se.enrollment_id) AS FLOAT) * 100, 2
        ) AS coverage_percentage
    FROM student_enrollment se
    INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
    INNER JOIN course c ON cc.course_id = c.course_id
    LEFT JOIN enrollment_draft_grade edg ON se.enrollment_id = edg.enrollment_id
    LEFT JOIN enrollment_grade_version egv ON cc.course_class_id = egv.course_class_id
    LEFT JOIN enrollment_grade_detail egd ON egv.grade_version_id = egd.grade_version_id 
        AND se.enrollment_id = egd.enrollment_id
    WHERE c.semester_id = @SummerSemesterId
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
) AS coverage_stats;