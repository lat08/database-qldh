USE EduManagement;
GO

-- ============================================================
-- SIMPLE QUERY TO CHECK TEST STUDENT DUPLICATE ENROLLMENTS
-- ============================================================
-- This query identifies test students with duplicate subject enrollments
-- Returns results only if duplicates are found

WITH TestStudentDuplicates AS (
    SELECT 
        s.student_code,
        p.full_name AS student_name,
        subj.subject_code,
        subj.subject_name,
        COUNT(DISTINCT se.course_class_id) AS enrollment_count,
        STRING_AGG(
            CONCAT(sem.semester_name, ' (', cc.date_start, ')'), 
            ', '
        ) AS enrolled_semesters
    FROM 
        student s
        INNER JOIN person p ON s.person_id = p.person_id
        INNER JOIN student_enrollment se ON s.student_id = se.student_id
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject subj ON c.subject_id = subj.subject_id
        INNER JOIN semester sem ON c.semester_id = sem.semester_id
    WHERE 
        -- Test students identified by their specific codes
        s.student_code IN ('SV999999', 'SV001', 'SV007', 'SV008')
        AND se.is_deleted = 0
        AND se.is_active = 1
        AND se.enrollment_status IN ('registered', 'completed')
        AND cc.is_deleted = 0
        AND cc.is_active = 1
    GROUP BY 
        s.student_code,
        p.full_name,
        subj.subject_code,
        subj.subject_name
    HAVING 
        COUNT(DISTINCT se.course_class_id) > 1  -- Only subjects with multiple enrollments
)
SELECT 
    student_code,
    student_name,
    subject_code,
    subject_name,
    enrollment_count AS duplicate_enrollments,
    enrolled_semesters
FROM TestStudentDuplicates
ORDER BY 
    student_code, 
    subject_code;

-- If no results are returned, test students have no duplicate enrollments!

GO