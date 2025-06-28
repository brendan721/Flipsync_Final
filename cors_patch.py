
# Simple CORS fix - replace the existing CORS middleware with browser-friendly config
import re

def fix_cors_in_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and replace the CORS middleware configuration
    cors_pattern = r'app\.add_middleware\(\s*CORSMiddleware,.*?\)'
    
    new_cors = """app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"], 
        expose_headers=["*"],
        max_age=600,
    )"""
    
    content = re.sub(cors_pattern, new_cors, content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    return True

# Apply the fix
fix_cors_in_file("fs_agt_clean/app/main.py")
print("✅ Applied simple CORS fix")
