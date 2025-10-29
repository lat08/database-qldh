# ==================== CONFIGURATION ====================
SPEC_FILE = r'database-qldh\specs.txt' 
OUTPUT_FILE = r'database-qldh\insert_data_temp.sql'

# ==================== MEDIA CONFIGURATION ====================
SUPABASE_BASE_URL = "https://baygtczqmdoolsvkxgpr.supabase.co/storage/v1/object/public"

MEDIA_BUCKETS = {
    'profile_pics': 'profile_pics',
    'instructor_documents': 'instructor_documents/demo',
    'room_pics': 'room_pics',
    'exams': 'exams/demo',
    'regulations': 'regulations'
}

MEDIA_BASE_PATH = R'medias'