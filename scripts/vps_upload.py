import pexpect
import sys
import os

HOST = "triyono@31.97.221.43"
PASSWORD = "*Admin123#"

def upload_file(local_path, remote_path):
    child = pexpect.spawn(f'scp -o StrictHostKeyChecking=no {local_path} {HOST}:{remote_path}')
    index = child.expect(['(?i)password:', pexpect.EOF, pexpect.TIMEOUT])
    if index == 0:
        child.sendline(PASSWORD)
        child.expect(pexpect.EOF)
    
    output = child.before.decode('utf-8')
    print(f"DEBUG: SCP Output: {output}")
    print(f"Uploaded {local_path} to {remote_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 vps_upload.py <local_path> <remote_path>")
        sys.exit(1)
    upload_file(sys.argv[1], sys.argv[2])
