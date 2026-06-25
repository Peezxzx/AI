s1 = r"C:\\Users\\Administrator\\Desktop\\bridge_mt5_session_opt_result.json"
s2 = r"C:\Users\Administrator\Desktop\bridge_mt5_session_opt_result.json"
print("ea version path:", repr(s1))
print("correct path:   ", repr(s2))
print()
# Does the ea version path actually work? Let's try writing to it.
from pathlib import Path
import os
p1 = Path(s1)
p2 = Path(s2)
print("ea path str:", str(p1))
print("correct path str:", str(p2))
print("are the same?", str(p1) == str(p2))
