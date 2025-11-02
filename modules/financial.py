import random
from datetime import date, timedelta
from collections import defaultdict
from .config import *

def create_student_health_insurance(self):
    """
    UPDATED: Store insurance IDs for payment generation
    Now tracks insurance records that will be paid via payment_insurance table
    REMOVED: is_paid column (no longer in schema)
    """
    self.add_statement("\n-- ==================== STUDENT HEALTH INSURANCE ====================")
    
    insurance_rows = []
    insurance_fee = 500000  # 500,000 VND per year
    
    # IMPORTANT: Initialize insurances list
    self.data['insurances'] = []
    
    # Build academic year date lookup from semesters
    ay_dates = {}
    for semester in self.data['semesters']:
        ay_id = semester['academic_year_id']
        if ay_id not in ay_dates:
            ay_dates[ay_id] = {
                'start_date': semester['start_date'],
                'end_date': semester['end_date']
            }
        else:
            if semester['start_date'] < ay_dates[ay_id]['start_date']:
                ay_dates[ay_id]['start_date'] = semester['start_date']
            if semester['end_date'] > ay_dates[ay_id]['end_date']:
                ay_dates[ay_id]['end_date'] = semester['end_date']
    
    for student in self.data['students']:
        student_start_year = student['class_start_year']
        
        for ay in self.data['academic_years']:
            if ay['start_year'] >= student_start_year and ay['start_year'] <= 2025:
                insurance_id = self.generate_uuid()
                
                dates = ay_dates.get(ay['academic_year_id'])
                if not dates:
                    start_date = date(ay['start_year'], 9, 1)
                    end_date = date(ay['end_year'], 8, 31)
                else:
                    start_date = dates['start_date']
                    end_date = dates['end_date']
                
                # Determine if this insurance should have a payment record
                should_have_payment = (ay['start_year'] <= 2024)  # Only past years are paid
                status = 'active' if ay['end_year'] >= 2025 else 'expired'
                
                insurance_rows.append([
                    insurance_id,
                    student['student_id'],
                    ay['academic_year_id'],
                    insurance_fee,
                    start_date,
                    end_date,
                    status
                ])
                
                # STORE insurance data for payment generation
                self.data['insurances'].append({
                    'insurance_id': insurance_id,
                    'student_id': student['student_id'],
                    'academic_year_id': ay['academic_year_id'],
                    'fee': insurance_fee,
                    'start_date': start_date,
                    'should_have_payment': should_have_payment
                })
    
    self.add_statement(f"-- Total health insurance records: {len(insurance_rows)}")
    
    self.bulk_insert('student_health_insurance',
                    ['insurance_id', 'student_id', 'academic_year_id', 'insurance_fee',
                    'start_date', 'end_date', 'insurance_status'],
                    insurance_rows)

def create_payments(self):
    """
    Generate payments for ~70% of enrollments (realistic unpaid scenarios)
    """
    self.add_statement("\n-- ==================== PAYMENTS ====================")
    self.add_statement("-- Payment rate: ~70% paid, ~30% unpaid (for testing)")
    
    enrollment_payment_rows = []
    enrollment_detail_rows = []
    insurance_payment_rows = []
    
    ENROLLMENT_PAYMENT_RATE = 0.70
    INSURANCE_PAYMENT_RATE = 0.90
    
    # Validate critical data exists
    total_enrollments = len(self.data.get('enrollments', []))
    total_course_classes = len(self.data.get('course_classes', []))
    total_curriculum_details = len(self.data.get('curriculum_details', []))
    
    if total_enrollments == 0:
        raise RuntimeError(
            f"CRITICAL ERROR: No enrollments found!\n"
            f"  Total enrollments: {total_enrollments}\n"
            f"  Total course_classes: {total_course_classes}\n"
            f"  Total curriculum_details: {total_curriculum_details}\n"
            f"PROBABLE CAUSES:\n"
            f"  - curriculum_details is empty (subjects not mapped to curricula)\n"
            f"  - course_classes is empty (no classes scheduled)\n"
            f"  - Enrollment logic failed to create any enrollments\n"
            f"CHECK: create_subjects(), create_curricula(), create_curriculum_details()"
        )
    
    # Group enrollments by student and semester
    enrollments_by_student_semester = defaultdict(list)
    
    for enrollment in self.data['enrollments']:
        if enrollment.get('status') in ['completed', 'registered']:
            course_class = next((cc for cc in self.data['course_classes'] 
                            if cc['course_class_id'] == enrollment['course_class_id']), None)
            if course_class:
                key = (enrollment['student_id'], course_class['semester_id'])
                enrollments_by_student_semester[key].append(enrollment)
    
    total_combinations = len(enrollments_by_student_semester)
    
    if total_combinations == 0:
        raise RuntimeError(
            f"CRITICAL ERROR: No valid student-semester combinations found!\n"
            f"  Total enrollments exist: {total_enrollments}\n"
            f"  But no enrollments have matching course_classes\n"
            f"PROBABLE CAUSE: course_class_id foreign key mismatch\n"
            f"CHECK: Verify enrollment course_class_ids match actual course_class records"
        )
    
    paid_count = 0
    
    for (student_id, semester_id), enrollments in enrollments_by_student_semester.items():
        # Random decision: should this student-semester have payment?
        if random.random() > ENROLLMENT_PAYMENT_RATE:
            continue
        
        paid_count += 1
        payment_id = self.generate_uuid()
        
        first_enrollment_date = min(e['enrollment_date'] for e in enrollments)
        payment_date = first_enrollment_date + timedelta(days=random.randint(1, 15))
        transaction_ref = f"TXN{random.randint(100000000, 999999999)}"
        
        enrollment_payment_rows.append([
            payment_id,
            student_id,
            semester_id,
            payment_date,
            transaction_ref,
            'completed',
            f'Thanh toán học phí học kỳ'
        ])
        
        for enr in enrollments:
            detail_id = self.generate_uuid()
            course = next((c for c in self.data['courses'] 
                        if c['course_id'] == enr['course_id']), None)
            
            if course:
                credits = course.get('credits', 0)
                fee_per_credit = float(self.course_config.get('fee_per_credit', 600000))
                amount_paid = credits * fee_per_credit
                
                enrollment_detail_rows.append([
                    detail_id,
                    payment_id,
                    enr['enrollment_id'],
                    amount_paid
                ])
    
    self.add_statement(f"-- Enrollment payments: {paid_count}/{total_combinations} ({paid_count/total_combinations*100:.1f}%)")
    
    # Insurance payments
    insurance_paid_count = 0
    insurance_total = 0
    
    for insurance in self.data.get('insurances', []):
        if insurance.get('should_have_payment', False):
            insurance_total += 1
            
            if random.random() > INSURANCE_PAYMENT_RATE:
                continue
            
            insurance_paid_count += 1
            payment_id = self.generate_uuid()
            payment_date = insurance['start_date'] - timedelta(days=random.randint(7, 30))
            
            insurance_payment_rows.append([
                payment_id,
                insurance['insurance_id'],
                payment_date,
                'completed',
                'Thanh toán bảo hiểm y tế sinh viên'
            ])
    
    if insurance_total > 0:
        self.add_statement(f"-- Insurance payments: {insurance_paid_count}/{insurance_total} ({insurance_paid_count/insurance_total*100:.1f}%)")
    
    self.bulk_insert('payment_enrollment',
                    ['payment_id', 'student_id', 'semester_id', 'payment_date', 
                    'transaction_reference', 'payment_status', 'notes'],
                    enrollment_payment_rows)
    
    self.bulk_insert('payment_enrollment_detail',
                    ['payment_enrollment_detail_ID', 'payment_id', 'enrollment_id', 
                    'amount_paid'],
                    enrollment_detail_rows)
    
    self.bulk_insert('payment_insurance',
                    ['payment_id', 'insurance_id', 'payment_date', 'payment_status', 'notes'],
                    insurance_payment_rows)
    
from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_student_health_insurance = create_student_health_insurance
SQLDataGenerator.create_payments = create_payments