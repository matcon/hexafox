import os
import requests
import sys

# Configure environment
BASE_URL = "http://127.0.0.1:8000"
USERNAME = "admin"
PASSWORD = "adminpassword123"

def create_test_files():
    # Create orig.bin with 16 bytes
    with open("orig.bin", "wb") as f:
        f.write(b'\x00' * 16)
    
    # Create mod.bin with one byte difference at offset 0x01
    with open("mod.bin", "wb") as f:
        f.write(b'\x00\xFF' + b'\x00' * 14)

    # Create target.bin (same as orig for test)
    with open("target.bin", "wb") as f:
        f.write(b'\x00' * 16)

def test_flow():
    session = requests.Session()
    
    print("[*] Testing Login API...")
    try:
        resp = session.post(f"{BASE_URL}/api/token/", json={
            "username": USERNAME,
            "password": PASSWORD
        })
        if resp.status_code != 200:
            print(f"[!] Login Failed: {resp.text}")
            return False
        
        tokens = resp.json()
        access_token = tokens['access']
        print("[+] Login Successful. Token obtained.")
    except Exception as e:
        print(f"[!] Connection Error: {e}")
        return False

    print("\n[*] Testing Compare API...")
    files = {
        'original': open('orig.bin', 'rb'),
        'modified': open('mod.bin', 'rb')
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    
    resp = session.post(f"{BASE_URL}/app/api/compare/", files=files, headers=headers)
    
    if resp.status_code != 200:
        print(f"[!] Compare Failed: {resp.text}")
        return False
    
    data = resp.json()
    diffs = data.get('diffs', [])
    patch_data = data.get('patch', {})
    
    if len(diffs) == 1 and patch_data.get('1') == 255: # '1' string key from JSON, 255 is 0xFF
        print(f"[+] Compare Verification Passed. Diff found at offset 0x01.")
    else:
        print(f"[!] Compare Verification Failed: {data}")
        return False
        
    print("\n[*] Testing Patch API...")
    patch_files = {'target': open('target.bin', 'rb')}
    patch_payload = {'patch': requests.mock_json_string(patch_data)} if False else patch_data 
    # requests data param handles dict as form fields, but we need to send JSON string for 'patch' field usually?
    # actually my view handles both json str and simple dict from data.
    # In requests, if I use 'data' with a dict it sends form-urlencoded.
    # If I use 'json' it sends body.
    # But I am sending FILES too, so it must be multipart/form-data.
    # In multipart, non-file fields are sent as strings.
    
    import json
    files_patch = {
        'target': open('target.bin', 'rb'),
    }
    data_patch = {
        'patch': json.dumps(patch_data)
    }
    
    resp = session.post(f"{BASE_URL}/app/api/patch/", files=files_patch, data=data_patch, headers=headers)
    
    if resp.status_code != 200:
        print(f"[!] Patch Failed: {resp.text}")
        return False
        
    with open("patched_result.bin", "wb") as f:
        f.write(resp.content)
        
    with open("patched_result.bin", "rb") as f:
        content = f.read()
        
    if content[1] == 0xFF:
        print("[+] Patch Verification Passed. File patched correctly.")
    else:
        print(f"[!] Patch Verification Failed. Byte 1 is {content[1]}")
        return False

    return True

if __name__ == "__main__":
    create_test_files()
    if test_flow():
        print("\nAll systems operational.")
        sys.exit(0)
    else:
        print("\nSystem check failed.")
        sys.exit(1)
