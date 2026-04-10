import os
import re

BASE_DIR = r"c:\Users\DELL\Desktop\college"
FILES_TO_PROCESS = [
    "core/views.py",
    "fees/views.py",
    "attendance/views.py",
    "academics/views.py",
    "accounts/views.py",
    "accounts/admin.py",
    "seed.py"
]

def refactor_file(filepath):
    path = os.path.join(BASE_DIR, filepath)
    if not os.path.exists(path):
        return
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    orig_content = content
    
    # Simple replacements
    content = re.sub(r'\.role\s*==\s*([\'"][a-zA-Z]+[\'"])', r'.role.name == \1', content)
    content = re.sub(r'\.role\s*!=\s*([\'"][a-zA-Z]+[\'"])', r'.role.name != \1', content)
    content = re.sub(r'\.role\s+in\s+([\[\(][^\)]+[\)\]])', r'.role.name in \1', content)
    content = re.sub(r'\.role\s+not\s+in\s+([\[\(][^\)]+[\)\]])', r'.role.name not in \1', content)
    
    # Specific filter logic
    content = content.replace("filter(role=", "filter(role__name=")
    content = content.replace("user__role=", "user__role__name=")
    
    # String formatting
    content = content.replace("{user.role}", "{user.role.name}")
    content = content.replace("user.role.name + '_dashboard.html'", "user.role.name + '_dashboard.html'") # actually they might use f"...{user.role}..."
    content = content.replace("role=user.role", "role=user.role.name")
    content = content.replace("role=request.user.role", "role=request.user.role.name")
    
    # Fix seed.py / create_user
    content = content.replace("role=role)", "role_name=role)")
    content = content.replace("role='student'", "role_name='student'")
    content = content.replace("role=role,", "role_name=role,")
    
    # Fix role map lookups (accounts/views.py)
    content = content.replace("role_map.get(user.role)", "role_map.get(user.role.name)")
    
    # accounts/views get user full name function was there, but we just use user.full_name now!
    # Let's cleanly replace `get_user_full_name(user)` with `user.full_name` anywhere
    content = content.replace("get_user_full_name(user)", "user.full_name")
    
    if orig_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Refactored: {filepath}")

for f in FILES_TO_PROCESS:
    refactor_file(f)
