USE EduManagement;
GO

-- ============================================================
-- Update all course fees to 1000
-- ============================================================
UPDATE course
SET fee_per_credit = 1000,
    updated_at = GETDATE()
WHERE is_deleted = 0;

-- Check the update result for courses
SELECT COUNT(*) AS total_courses_updated
FROM course
WHERE fee_per_credit = 1000 AND is_deleted = 0;

-- ============================================================
-- Update all subject credits to 1
-- ============================================================
UPDATE subject
SET credits = 1,
    updated_at = GETDATE()
WHERE is_deleted = 0;

-- Check the update result for subjects
SELECT COUNT(*) AS total_subjects_updated
FROM subject
WHERE credits = 1 AND is_deleted = 0;

GO

-- ============================================================
-- Optional: Display sample of updated records
-- ============================================================
SELECT TOP 10 
    course_id,
    subject_id,
    semester_id,
    fee_per_credit,
    updated_at
FROM course
WHERE is_deleted = 0
ORDER BY updated_at DESC;

SELECT TOP 10
    subject_id,
    subject_code,
    subject_name,
    credits,
    updated_at
FROM subject
WHERE is_deleted = 0
ORDER BY updated_at DESC;

GO