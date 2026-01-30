import os

HEX_WIDTH = 16

def printable(b):
    if b is None:
        return " "
    return chr(b) if 32 <= b <= 126 else "."

def patched_name(path):
    base, ext = os.path.splitext(path)
    return f"{base}_CLEARED_BY_JOMBERYKASO{ext}"

def compare_files_logic(orig_path, mod_path):
    """
    Compares two files and returns a list of differences.
    Each difference contains: offset, hex bytes (orig/mod), ascii (orig/mod).
    Also returns a patch dictionary {offset: new_byte}.
    """
    diffs = []
    patch = {}
    
    with open(orig_path, "rb") as fa, open(mod_path, "rb") as fb:
        offset = 0
        while True:
            a = fa.read(HEX_WIDTH)
            b = fb.read(HEX_WIDTH)
            if not a and not b:
                break

            # If chunks differ, analyze them byte by byte
            if a != b:
                row = {
                    "offset": f"{offset:08X}",
                    "hex_data": [],
                    "ascii_a": "",
                    "ascii_b": ""
                }
                
                for i in range(HEX_WIDTH):
                    ba = a[i] if i < len(a) else None
                    bb = b[i] if i < len(b) else None

                    # Patch Logic: If they differ and ba is not None (meaning not EOF of orig)
                    if ba != bb and ba is not None:
                         # Warning: The original script logic was:
                         # if ba != bb and ba is not None: patch[offset + i] = bb
                         # BUT, if bb is None, it means Mod is shorter. 
                         # We should probably handle that. For now, following original logic strictness.
                         if bb is not None:
                             patch[offset + i] = bb
                    
                    # Visual Logic
                    hx_a = f"{ba:02X}" if ba is not None else "--"
                    hx_b = f"{bb:02X}" if bb is not None else "--"
                    
                    is_diff = (ba != bb)
                    
                    row["hex_data"].append({
                        "a": hx_a, 
                        "b": hx_b, 
                        "diff": is_diff,
                        "val_b": bb # Store for potential patching usage if needed frontend side
                    })
                    
                    row["ascii_a"] += printable(ba)
                    row["ascii_b"] += printable(bb)
                    
                diffs.append(row)

            offset += HEX_WIDTH
            
    return {"diffs": diffs, "patch": patch}

def apply_patch_logic(target_path, patch_data):
    """
    Applies patch_data {offset: byte_val} to target_path.
    Returns the path to the new patched file and the modifications count.
    """
    with open(target_path, "rb") as f:
        data = bytearray(f.read())

    modifications = []
    
    # patch_data keys come as strings from JSON usually, ensure they are ints
    # and values are ints
    for off, val in patch_data.items():
        off_int = int(off)
        val_int = int(val)
        
        if off_int < len(data):
            old = data[off_int]
            data[off_int] = val_int
            modifications.append(f"0x{off_int:08X} : {old} -> {val_int}")
        else:
            modifications.append(f"0x{off_int:08X} : OUT OF BOUNDS (Skipped)")

    out_path = patched_name(target_path)
    with open(out_path, "wb") as f:
        f.write(data)
        
    return out_path, modifications
