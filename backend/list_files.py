import os
def get_size_mb(path):
    return round(os.path.getsize(path) / (1024 * 1024), 2)

base_dir = "uploads"
for root, dirs, files in os.walk(base_dir):
    for name in files:
        full_path = os.path.join(root, name)
        size = os.path.getsize(full_path)
        print(f"{full_path} | {size} bytes")
