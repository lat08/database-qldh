class SpecParser:
    def __init__(self, spec_file):
        self.spec_file = spec_file
        self.data = {}
        self.current_section = None
        
    def parse(self):
        with open(self.spec_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('[') and line.endswith(']'):
                    self.current_section = line[1:-1]
                    self.data[self.current_section] = []
                # IMPORTANT: Check for pipe FIRST (before colon)
                elif self.current_section and '|' in line:
                    self.data[self.current_section].append(line)
                # Then check for colon (config lines) - but EXCLUDE URLs
                elif self.current_section and ':' in line:
                    # Skip if line starts with http/https (URL)
                    if line.startswith('http://') or line.startswith('https://'):
                        self.data[self.current_section].append(line)
                    # Skip if line contains '://' anywhere (URL)
                    elif '://' in line:
                        self.data[self.current_section].append(line)
                    # Otherwise treat as config (key: value)
                    else:
                        key, value = line.split(':', 1)
                        self.data.setdefault(self.current_section + '_config', {})[key.strip()] = value.strip()
        
        return self.data