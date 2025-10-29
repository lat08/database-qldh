def create_roles_and_permissions(self):
    """
    Create roles, permissions, and role_permission mappings based on spec file
    """
    self.add_statement("\n-- ==================== ROLES ====================")
    
    role_rows = []
    permission_rows = []
    role_permission_rows = []
    
    # Track role IDs for later use
    role_id_map = {}
    permission_id_map = {}
    
    # =========================================================================
    # 1. CREATE ROLES
    # =========================================================================
    for line in self.spec_data.get('roles', []):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 2:
            continue
        
        role_name, description = parts[0], parts[1]
        role_id = self.generate_uuid()
        
        role_id_map[role_name] = role_id
        
        role_rows.append([role_id, role_name, description])
        
        self.add_statement(f"-- Role: {role_name}")
    
    self.bulk_insert('role', ['role_id', 'role_name', 'description'], role_rows)
    
    # =========================================================================
    # 2. CREATE PERMISSIONS
    # =========================================================================
    self.add_statement("\n-- ==================== PERMISSIONS ====================")
    
    for line in self.spec_data.get('permissions', []):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 2:
            continue
        
        permission_name, permission_description = parts[0], parts[1]
        permission_id = self.generate_uuid()
        
        permission_id_map[permission_name] = permission_id
        
        permission_rows.append([permission_id, permission_name, permission_description])
    
    self.bulk_insert('permission', 
                    ['permission_id', 'permission_name', 'permission_description'], 
                    permission_rows)
    
    # =========================================================================
    # 3. CREATE ROLE_PERMISSION MAPPINGS
    # =========================================================================
    self.add_statement("\n-- ==================== ROLE PERMISSIONS MAPPING ====================")
    
    for line in self.spec_data.get('role_permissions', []):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 2:
            continue
        
        role_name = parts[0]
        permission_names = [p.strip() for p in parts[1].split(',')]
        
        role_id = role_id_map.get(role_name)
        if not role_id:
            self.add_statement(f"-- WARNING: Role not found: {role_name}")
            continue
        
        for permission_name in permission_names:
            permission_id = permission_id_map.get(permission_name)
            if not permission_id:
                self.add_statement(f"-- WARNING: Permission not found: {permission_name}")
                continue
            
            role_permission_id = self.generate_uuid()
            role_permission_rows.append([role_permission_id, role_id, permission_id, True])
        
        self.add_statement(f"-- Mapped {len(permission_names)} permissions to {role_name}")
    
    self.bulk_insert('role_permission',
                    ['role_permission_id', 'role_id', 'permission_id', 'is_active'],
                    role_permission_rows)
    
    self.add_statement(f"\n-- Total roles: {len(role_rows)}")
    self.add_statement(f"-- Total permissions: {len(permission_rows)}")
    self.add_statement(f"-- Total role-permission mappings: {len(role_permission_rows)}")
    
    # Store role_id_map for later use
    self.role_id_map = role_id_map

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_roles_and_permissions = create_roles_and_permissions