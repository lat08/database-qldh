from .config import *
import random
import os

class MediaScanner:
    """Scans media folders and tracks available files"""
    def __init__(self, media_base_path):
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # If media_base_path is relative, make it relative to script location
        if not os.path.isabs(media_base_path):
            self.media_base_path = os.path.join(script_dir, media_base_path)
        else:
            self.media_base_path = media_base_path
            
        self.files = {
            'profile_pics': [],
            'course_docs': {'pdf': [], 'images': [], 'excel': []},
            'room_pics': [],
            'regulations': []
        }
        self.scan_files()
    
    def scan_files(self):
        """Scan all media folders and categorize files (recursively)"""
        print(f"\n{'='*70}")
        print(f"SCANNING MEDIA FOLDERS")
        print(f"{'='*70}")
        print(f"Base path: {os.path.abspath(self.media_base_path)}")
        print(f"{'='*70}\n")
        
        # Profile pictures - REQUIRED
        profile_path = os.path.join(self.media_base_path, 'profile_pics')
        profile_full_path = os.path.abspath(profile_path)
        print(f"[1] Searching: {profile_full_path}")
        
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"CRITICAL: Profile pictures folder not found!\n"
                                   f"Expected: {profile_full_path}\n"
                                   f"Please create this folder and add image files.")
        
        self.files['profile_pics'] = []
        for root, dirs, files in os.walk(profile_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    self.files['profile_pics'].append(file)
        
        if not self.files['profile_pics']:
            raise FileNotFoundError(f"CRITICAL: No image files found!\n"
                                   f"Searched in: {profile_full_path}\n"
                                   f"Add .jpg, .jpeg, .png, or .gif files to this folder.")
        
        print(f"    ✓ Found {len(self.files['profile_pics'])} profile pictures\n")
        
        # Course documents - REQUIRED
        course_docs_path = os.path.join(self.media_base_path, 'course_docs')
        course_docs_full_path = os.path.abspath(course_docs_path)
        print(f"[2] Searching: {course_docs_full_path}")
        
        if not os.path.exists(course_docs_path):
            raise FileNotFoundError(f"CRITICAL: Course documents folder not found!\n"
                                   f"Expected: {course_docs_full_path}\n"
                                   f"Please create this folder and add PDF/image/Excel files.")
        
        for root, dirs, files in os.walk(course_docs_path):
            for file in files:
                file_lower = file.lower()
                if file_lower.endswith('.pdf'):
                    self.files['course_docs']['pdf'].append(file)
                elif file_lower.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    self.files['course_docs']['images'].append(file)
                elif file_lower.endswith(('.xls', '.xlsx', '.xlsm')):
                    self.files['course_docs']['excel'].append(file)
        
        total_course_files = (len(self.files['course_docs']['pdf']) + 
                             len(self.files['course_docs']['images']) + 
                             len(self.files['course_docs']['excel']))
        if total_course_files == 0:
            raise FileNotFoundError(f"CRITICAL: No document files found!\n"
                                   f"Searched in: {course_docs_full_path}\n"
                                   f"Add PDF, image, or Excel files to this folder.")
        
        print(f"    ✓ Found {len(self.files['course_docs']['pdf'])} PDFs, "
              f"{len(self.files['course_docs']['images'])} images, "
              f"{len(self.files['course_docs']['excel'])} Excel files\n")
                
        # Room pictures - OPTIONAL (ignore if missing)
        room_pics_path = os.path.join(self.media_base_path, 'room_pics')
        room_pics_full_path = os.path.abspath(room_pics_path)
        print(f"[3] Searching: {room_pics_full_path}")
        
        if os.path.exists(room_pics_path):
            self.files['room_pics'] = []
            for root, dirs, files in os.walk(room_pics_path):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        self.files['room_pics'].append(file)
            print(f"    ✓ Found {len(self.files['room_pics'])} room pictures\n")
        else:
            print(f"    ⊘ Not found (optional)\n")
        
        # Regulations - FUCK IT (completely optional, skip silently)
        regulations_path = os.path.join(self.media_base_path, 'regulations')
        if os.path.exists(regulations_path):
            self.files['regulations'] = []
            for root, dirs, files in os.walk(regulations_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        self.files['regulations'].append(file)
        
        print(f"{'='*70}\n")
    
    def get_random_file(self, category, subcategory=None):
        """Get a random file from a category"""
        if subcategory:
            files = self.files.get(category, {}).get(subcategory, [])
        else:
            files = self.files.get(category, [])
        
        if files:
            return random.choice(files)
        return None
    
    def build_url(self, bucket_key, filename):
        """Build Supabase storage URL"""
        bucket_path = MEDIA_BUCKETS.get(bucket_key)
        if not bucket_path:
            return None
        return f"{SUPABASE_BASE_URL}/{bucket_path}/{filename}"
