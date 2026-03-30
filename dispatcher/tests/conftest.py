import os

# middleware.py modül yüklenirken JWT_SECRET'i okur — importtan önce set edilmeli
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
