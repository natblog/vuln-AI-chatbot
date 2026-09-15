import os
import tempfile

_db_dir = tempfile.mkdtemp(prefix="vulnlab-test-")
os.environ["DB_PATH"] = os.path.join(_db_dir, "test.db")
