import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_eud.sqlite3")
os.environ.setdefault("ADMIN_API_TOKEN", "test-secret-token")
os.environ.setdefault("LOCAL_STORAGE_ROOT", "/tmp/earth-under-decision-test-data")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
