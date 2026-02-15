import pexpect
import sys
import os

HOST = "triyono@31.97.221.43"
PASSWORD = "*Admin123#"

def run_vps_cmd(cmd):
    child = pexpect.spawn(f'ssh -o StrictHostKeyChecking=no {HOST} "{cmd}"')
    index = child.expect(['(?i)password:', pexpect.EOF, pexpect.TIMEOUT])
    print(f"DEBUG: index={index}")
    if index == 0:
        child.sendline(PASSWORD)
        child.expect(pexpect.EOF)
    output = child.before.decode('utf-8')
    print(f"DEBUG: output length={len(output)}")
    print(output)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 vps_exec.py '<command>'")
        sys.exit(1)
    run_vps_cmd(sys.argv[1])
