DECLARE @TestStudentEmail NVARCHAR(255) = 'student.test@edu.vn';
DECLARE @StudentId UNIQUEIDENTIFIER;
DECLARE @Fall2025SemesterStartDate DATE;

-- Get student ID
SELECT @StudentId = s.student_id 
FROM student s
INNER JOIN person p ON s.person_id = p.person_id
WHERE p.email = @TestStudentEmail;

-- Get Fall 2025-2026 semester start date
SELECT @Fall2025SemesterStartDate = s.start_date
FROM semester s
WHERE s.semester_name LIKE '%2025-2026%' 
  AND (s.semester_name LIKE '%1%' OR s.semester_name LIKE '%fall%' OR s.semester_name LIKE '%kỳ 1%')
  AND s.is_active = 1
  AND s.is_deleted = 0;

-- Create payments for all unpaid enrollments prior to Fall 2025-2026
DECLARE @UnpaidEnrollments TABLE (
    enrollment_id UNIQUEIDENTIFIER,
    semester_id UNIQUEIDENTIFIER,
    amount_owed DECIMAL(18,2)
);

-- Get all unpaid enrollments
INSERT INTO @UnpaidEnrollments
SELECT 
    se.enrollment_id,
    sem.semester_id,
    (c.fee_per_credit * sub.credits) - ISNULL((
        SELECT SUM(ped.amount_paid)
        FROM payment_enrollment pe
        INNER JOIN payment_enrollment_detail ped ON pe.payment_id = ped.payment_id
        WHERE ped.enrollment_id = se.enrollment_id
          AND pe.payment_status = 'completed'
          AND pe.is_active = 1
          AND pe.is_deleted = 0
          AND ped.is_deleted = 0
    ), 0) as amount_owed
FROM semester sem
INNER JOIN course c ON sem.semester_id = c.semester_id
INNER JOIN course_class cc ON c.course_id = cc.course_id
INNER JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
INNER JOIN subject sub ON c.subject_id = sub.subject_id
WHERE se.student_id = @StudentId
  AND sem.start_date < @Fall2025SemesterStartDate
  AND sem.is_active = 1
  AND sem.is_deleted = 0
  AND c.is_active = 1
  AND c.is_deleted = 0
  AND cc.is_active = 1
  AND cc.is_deleted = 0
  AND se.is_active = 1
  AND se.is_deleted = 0
  -- Only unpaid enrollments
  AND (c.fee_per_credit * sub.credits) > ISNULL((
      SELECT SUM(ped.amount_paid)
      FROM payment_enrollment pe
      INNER JOIN payment_enrollment_detail ped ON pe.payment_id = ped.payment_id
      WHERE ped.enrollment_id = se.enrollment_id
        AND pe.payment_status = 'completed'
        AND pe.is_active = 1
        AND pe.is_deleted = 0
        AND ped.is_deleted = 0
  ), 0);

-- Create payment records for each semester with unpaid enrollments
DECLARE @SemesterId UNIQUEIDENTIFIER;
DECLARE @PaymentId UNIQUEIDENTIFIER;

DECLARE semester_cursor CURSOR FOR
SELECT DISTINCT semester_id FROM @UnpaidEnrollments;

OPEN semester_cursor;
FETCH NEXT FROM semester_cursor INTO @SemesterId;

WHILE @@FETCH_STATUS = 0
BEGIN
    -- Create payment_enrollment record
    SET @PaymentId = NEWID();
    
    INSERT INTO payment_enrollment (
        payment_id,
        student_id,
        semester_id,
        payment_status,
        notes,
        payment_date,
        created_at,
        is_active,
        is_deleted
    )
    VALUES (
        @PaymentId,
        @StudentId,
        @SemesterId,
        'completed',
        'Bulk payment for unpaid enrollments prior to Fall 2025-2026',
        GETDATE(),
        GETDATE(),
        1,
        0
    );
    
    -- Create payment_enrollment_detail records for this semester
    INSERT INTO payment_enrollment_detail (
        payment_enrollment_detail_id,
        payment_id,
        enrollment_id,
        amount_paid,
        created_at,
        is_deleted
    )
    SELECT 
        NEWID(),
        @PaymentId,
        ue.enrollment_id,
        ue.amount_owed,
        GETDATE(),
        0
    FROM @UnpaidEnrollments ue
    WHERE ue.semester_id = @SemesterId;
    
    FETCH NEXT FROM semester_cursor INTO @SemesterId;
END;

CLOSE semester_cursor;
DEALLOCATE semester_cursor;

-- Show summary of what was paid
SELECT 
    sem.semester_name,
    sem.start_date,
    COUNT(ue.enrollment_id) as enrollments_paid,
    SUM(ue.amount_owed) as total_amount_paid
FROM @UnpaidEnrollments ue
INNER JOIN semester sem ON ue.semester_id = sem.semester_id
GROUP BY sem.semester_id, sem.semester_name, sem.start_date
ORDER BY sem.start_date DESC;

PRINT 'Payment completed for all unpaid enrollments prior to Fall 2025-2026';