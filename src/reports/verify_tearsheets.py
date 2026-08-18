import os

files = [f for f in os.listdir("reports/tearsheets") if f.endswith("_tearsheet.pdf")]
print(f"Tearsheet PDF count: {len(files)}")

small_files = []
for f in files:
    size_kb = os.path.getsize(f"reports/tearsheets/{f}") / 1024
    if size_kb < 30:
        small_files.append((f, round(size_kb, 1)))

print(f"Files under 30 KB: {len(small_files)}")
if small_files:
    print(small_files)