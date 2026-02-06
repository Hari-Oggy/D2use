"""Test only the critical summary"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "tests.test_comprehensive_validation"],
    capture_output=True,
    text=True,
    cwd=r"e:\additional\D2use"
)

# Extract just the summary
lines = result.stdout.split("\n")
summary_started = False
for line in lines:
    if "VALIDATION SUMMARY" in line:
        summary_started = True
    if summary_started:
        print(line)
