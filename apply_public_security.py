"""
Apply Public Security (No Auth) Script
"""

import os
import shutil
from datetime import datetime

def backup_file(filepath):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup: {backup_path}")
    return backup_path

def apply_public_security():
    main_py = "app/main.py"
    
    print("=" * 70)
    print("🔐 APPLYING PUBLIC SECURITY (NO AUTH)")
    print("=" * 70)
    print()
    
    if not os.path.exists(main_py):
        print(f"❌ {main_py} not found")
        return False
    
    backup_file(main_py)
    
    with open(main_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update imports - use public version
    if "from app.api import chat, auth" in content:
        content = content.replace(
            "from app.api import chat, auth",
            "from app.api import chat_public as chat"
        )
        print("✅ Updated to public chat (no auth)")
    
    # Add security middleware import
    if "from app.middleware.security import SecurityMiddleware" not in content:
        content = content.replace(
            "from app.middleware.error_handler import (",
            "from app.middleware.security import SecurityMiddleware\nfrom app.middleware.error_handler import ("
        )
        print("✅ Added SecurityMiddleware import")
    
    # Add security middleware
    if "app.add_middleware(SecurityMiddleware)" not in content:
        cors_section = """app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # ← FIXED: Use cors_origins_list property
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""
        
        new_section = cors_section + "\n\n# Security Middleware\napp.add_middleware(SecurityMiddleware)"
        content = content.replace(cors_section, new_section)
        print("✅ Added SecurityMiddleware")
    
    # Remove auth router
    if 'app.include_router(auth.router' in content:
        lines = content.split('\n')
        new_lines = [line for line in lines if 'auth.router' not in line]
        content = '\n'.join(new_lines)
        print("✅ Removed auth router (not needed)")
    
    with open(main_py, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print()
    print("=" * 70)
    print("✅ PUBLIC SECURITY APPLIED!")
    print("=" * 70)
    print()
    print("🔐 Security Features:")
    print("   ✅ Input validation (XSS, SQL injection, path traversal)")
    print("   ✅ Security headers (XSS protection, clickjacking)")
    print("   ✅ Rate limiting (20 requests/day per session)")
    print("   ✅ Request size limits (max 2000 chars)")
    print("   ✅ Log sanitization")
    print()
    print("❌ Disabled:")
    print("   - Authentication (no login required)")
    print("   - Student data access")
    print()
    print("🚀 Next: python -m app.main")
    print()
    
    return True

if __name__ == "__main__":
    try:
        apply_public_security()
    except Exception as e:
        print(f"❌ Error: {e}")
