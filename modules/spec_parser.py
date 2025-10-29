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
                # This prevents URLs with colons from being parsed as config
                elif self.current_section and '|' in line:
                    self.data[self.current_section].append(line)
                # Then check for colon (for config lines)
                elif self.current_section and ':' in line:
                    # Make sure it's a config line (key: value format)
                    if line.count(':') >= 1 and not line.startswith('http'):
                        key, value = line.split(':', 1)
                        self.data.setdefault(self.current_section + '_config', {})[key.strip()] = value.strip()
        
        return self.data
    