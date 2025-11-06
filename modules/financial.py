import random
from datetime import date, timedelta, datetime
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
    REVISED: Create payments for 10% of enrollments (was 50%)
    """
    self.add_statement("\n-- ==================== PAYMENTS ====================")
    self.add_statement("-- Payment rate: 10% of enrollments")
    
    payment_enrollment_rows = []
    payment_detail_rows = []
    
    # Group enrollments by student and semester
    enrollments_by_student_semester = defaultdict(list)
    for enrollment in self.data['enrollments']:
        key = (enrollment['student_id'], enrollment['semester_id'])
        enrollments_by_student_semester[key].append(enrollment)
    
    total_paid_enrollments = 0
    total_payments = 0
    
    for (student_id, semester_id), enrollments in enrollments_by_student_semester.items():
        # CHANGED: 10% chance of payment (was 50%)
        if random.random() > 0.10:
            continue
        
        payment_id = self.generate_uuid()
        total_payments += 1
        
        # Payment date: random within semester
        semester = next((s for s in self.data['semesters'] if s['semester_id'] == semester_id), None)
        if semester:
            sem_start = semester['start_date']
            sem_end = semester['end_date']
            if isinstance(sem_start, str):
                sem_start = datetime.strptime(sem_start, '%Y-%m-%d').date()
            if isinstance(sem_end, str):
                sem_end = datetime.strptime(sem_end, '%Y-%m-%d').date()
            
            payment_date = sem_start + timedelta(days=random.randint(0, (sem_end - sem_start).days))
        else:
            payment_date = date.today()
        
        # Create payment record
        payment_enrollment_rows.append([
            payment_id,
            student_id,
            semester_id,
            payment_date,
            f'TXN{random.randint(100000, 999999)}',
            'completed',
            'Course enrollment payment'
        ])
        
        # Create payment details for each enrollment
        for enrollment in enrollments:
            payment_detail_id = self.generate_uuid()
            
            # Calculate amount
            course = next((c for c in self.data['courses'] 
                          if c['course_id'] == enrollment['course_id']), None)
            if course:
                amount = course['credits'] * 600000  # fee_per_credit
            else:
                amount = 3 * 600000  # default
            
            payment_detail_rows.append([
                payment_detail_id,
                payment_id,
                enrollment['enrollment_id'],
                amount
            ])
            
            total_paid_enrollments += 1
    
    self.add_statement(f"-- Total payments: {total_payments}")
    self.add_statement(f"-- Total paid enrollments: {total_paid_enrollments}")
    self.add_statement(f"-- Payment rate: {(total_paid_enrollments / len(self.data['enrollments']) * 100):.1f}%")
    
    self.bulk_insert('payment_enrollment',
                    ['payment_id', 'student_id', 'semester_id', 'payment_date',
                     'transaction_reference', 'payment_status', 'notes'],
                    payment_enrollment_rows)
    
    if payment_detail_rows:
        self.bulk_insert('payment_enrollment_detail',
                        ['payment_enrollment_detail_ID', 'payment_id', 'enrollment_id', 'amount_paid'],
                        payment_detail_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_student_health_insurance = create_student_health_insurance
SQLDataGenerator.create_payments = create_payments