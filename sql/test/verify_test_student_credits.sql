-- ============================================================
-- VERIFY TEST STUDENT CREDITS
-- ============================================================
-- This query calculates credit information for test student (student.test@edu.vn):
-- 1. Total credits in student curriculum
-- 2. Total credits in the curriculum that the student have earned
-- 3. Total credits outside the curriculum
-- 4. Total credits student have earned including both
-- 5. Credits in curriculum left

USE EduManagement;
GO

DECLARE @TestStudentEmail VARCHAR(255) = 'student.test@edu.vn';

-- Get test student info
DECLARE @StudentId UNIQUEIDENTIFIER;
DECLARE @CurriculumId UNIQUEIDENTIFIER;

SELECT 
    @StudentId = s.student_id,
    @CurriculumId = c.curriculum_id
FROM student s
INNER JOIN person p ON s.person_id = p.person_id
LEFT JOIN class c ON s.class_id = c.class_id
WHERE p.email = @TestStudentEmail;

IF @StudentId IS NOT NULL
BEGIN
    ;WITH StudentCurriculumSubjects AS (
        SELECT DISTINCT s.subject_id, s.credits
        FROM curriculum_detail cd
        INNER JOIN subject s ON cd.subject_id = s.subject_id
        WHERE cd.curriculum_id = @CurriculumId
            AND cd.is_active = 1
            AND cd.is_deleted = 0
            AND s.is_active = 1
            AND s.is_deleted = 0
    ),
    StudentEnrollmentsWithGrades AS (
        SELECT 
            s.subject_id,
            s.credits,
            CASE 
                WHEN egd.attendance_grade IS NOT NULL 
                    AND egd.midterm_grade IS NOT NULL 
                    AND egd.final_grade IS NOT NULL
                THEN (egd.attendance_grade * 0.1 + egd.midterm_grade * 0.3 + egd.final_grade * 0.6)
                ELSE NULL
            END AS final_grade,
            egv.version_number,
            ROW_NUMBER() OVER (
                PARTITION BY se.student_id, s.subject_id 
                ORDER BY egv.version_number DESC
            ) AS rn
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN enrollment_grade_detail egd ON se.enrollment_id = egd.enrollment_id
        INNER JOIN enrollment_grade_version egv ON egd.grade_version_id = egv.grade_version_id
        WHERE se.student_id = @StudentId
            AND se.enrollment_status IN ('registered', 'completed')
            AND se.is_active = 1
            AND se.is_deleted = 0
            AND egv.version_status = 'approved'
    ),
    LatestGrades AS (
        SELECT *
        FROM StudentEnrollmentsWithGrades
        WHERE rn = 1
    ),
    PassedInCurriculum AS (
        SELECT lg.subject_id, lg.credits
        FROM LatestGrades lg
        INNER JOIN StudentCurriculumSubjects scs ON lg.subject_id = scs.subject_id
        WHERE lg.final_grade >= 5.0
    ),
    PassedOutsideCurriculum AS (
        SELECT lg.subject_id, lg.credits
        FROM LatestGrades lg
        WHERE lg.final_grade >= 5.0
            AND lg.subject_id NOT IN (SELECT subject_id FROM StudentCurriculumSubjects)
    )
    SELECT 
        (SELECT ISNULL(SUM(credits), 0) FROM StudentCurriculumSubjects) AS total_curriculum_credits,
        (SELECT ISNULL(SUM(credits), 0) FROM PassedInCurriculum) AS earned_in_curriculum,
        (SELECT ISNULL(SUM(credits), 0) FROM PassedOutsideCurriculum) AS earned_outside_curriculum,
        (
            (SELECT ISNULL(SUM(credits), 0) FROM PassedInCurriculum) +
            (SELECT ISNULL(SUM(credits), 0) FROM PassedOutsideCurriculum)
        ) AS total_earned_credits,
        (
            (SELECT ISNULL(SUM(credits), 0) FROM StudentCurriculumSubjects) -
            (SELECT ISNULL(SUM(credits), 0) FROM PassedInCurriculum)
        ) AS credits_left_in_curriculum;
END
ELSE
BEGIN
    SELECT 'Student not found' AS error;
END
