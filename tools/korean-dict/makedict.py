# Builds a HeliBoard / AOSP binary dictionary (format version 202) for Korean.
# Words are stored as decomposed standard jamo (NFD), which is what HeliBoard's KoreanDictionary looks up.
# usage: makedict.py <frequency list "word count" per line> <out.dict> [max words]
import math, re, sys, time, unicodedata

src, out = sys.argv[1], sys.argv[2]
max_words = int(sys.argv[3]) if len(sys.argv) > 3 else 150000
MIN_COUNT = 3

# words containing these are marked possibly offensive (hidden while "block offensive words" is on)
OFFENSIVE = ["씨발", "씨빨", "씨팔", "시발", "시팔", "씨바", "씨벌", "씹", "좆", "존나", "졸라", "병신", "븅신", "빙신",
             "지랄", "개새", "개세", "썅", "니미", "니애미", "느금", "엿먹", "닥쳐", "미친놈", "미친년", "염병", "꺼져",
             "새끼", "쌍년", "쌍놈", "개년", "개놈", "창녀", "걸레년"]

hangul = re.compile(r"^[가-힣]+$")
words = []
with open(src, encoding="utf-8") as f:
    for line in f:
        parts = line.split()
        if len(parts) != 2:
            continue
        w, c = parts[0], int(parts[1])
        if c < MIN_COUNT or not hangul.match(w):
            continue
        words.append((w, c))
        if len(words) >= max_words:
            break

max_log = math.log(words[0][1])
entries = {}
for w, c in words:
    prob = max(1, min(255, round(255 * math.log(c) / max_log)))
    key = unicodedata.normalize("NFD", w)
    offensive = any(o in w for o in OFFENSIVE)
    if key not in entries:
        entries[key] = (prob, offensive)

# --- trie ---
class Node:
    __slots__ = ("chars", "children", "prob", "offensive")
    def __init__(self, chars):
        self.chars = chars
        self.children = {}
        self.prob = None
        self.offensive = False

root = Node("")
for key, (prob, off) in entries.items():
    n = root
    for ch in key:
        n = n.children.setdefault(ch, Node(ch))
    n.prob, n.offensive = prob, off

def compress(n):
    for k, c in list(n.children.items()):
        while c.prob is None and len(c.children) == 1:
            (only,) = c.children.values()
            c.chars += only.chars
            c.children = only.children
            c.prob, c.offensive = only.prob, only.offensive
        n.children[k] = c
        compress(c)
sys.setrecursionlimit(100000)
compress(root)

def enc_char(cp):
    if 0x20 <= cp <= 0xFF:
        return bytes([cp])
    return cp.to_bytes(3, "big")

def node_size(c):
    s = 1 + sum(len(enc_char(ord(ch))) for ch in c.chars)
    if len(c.chars) > 1:
        s += 1
    if c.prob is not None:
        s += 1
    if c.children:
        s += 3
    return s

def array_size(arr):
    return (1 if len(arr) < 0x80 else 2) + sum(node_size(c) for c in arr)

# lay out node arrays breadth first, so children always come after their parent
arrays = []
queue = [sorted(root.children.values(), key=lambda c: c.chars)]
while queue:
    arr = queue.pop(0)
    arrays.append(arr)
    for c in arr:
        if c.children:
            queue.append(sorted(c.children.values(), key=lambda x: x.chars))

def header_string(s):
    return b"".join(enc_char(ord(ch)) for ch in s) + b"\x1f"

attrs = {"date": str(int(time.time())), "dictionary": "main:ko", "locale": "ko", "version": "2",
         "description": "한국어 (FrequencyWords)"}
attr_bytes = b"".join(header_string(k) + header_string(v) for k, v in attrs.items())
header_size = 12 + len(attr_bytes)

pos = header_size
array_pos = {}
for arr in arrays:
    array_pos[id(arr)] = pos
    pos += array_size(arr)
# map node -> position of its children array
child_array_of = {}
for arr in arrays:
    for c in arr:
        pass
# arrays were appended in the same order the children were queued
idx = 1
for arr in arrays:
    for c in arr:
        if c.children:
            child_array_of[id(c)] = array_pos[id(arrays[idx])]
            idx += 1

buf = bytearray()
buf += bytes.fromhex("9bc13afe") + (202).to_bytes(2, "big") + b"\x00\x00" + header_size.to_bytes(4, "big") + attr_bytes
for arr in arrays:
    assert len(buf) == array_pos[id(arr)]
    n = len(arr)
    buf += bytes([n]) if n < 0x80 else (0x8000 | n).to_bytes(2, "big")
    for c in arr:
        flags = 0
        if c.children: flags |= 0xC0
        if len(c.chars) > 1: flags |= 0x20
        if c.prob is not None: flags |= 0x10
        if c.offensive: flags |= 0x01
        buf.append(flags)
        for ch in c.chars:
            buf += enc_char(ord(ch))
        if len(c.chars) > 1:
            buf.append(0x1F)
        if c.prob is not None:
            buf.append(c.prob)
        if c.children:
            field = len(buf)
            buf += (child_array_of[id(c)] - field).to_bytes(3, "big")
open(out, "wb").write(buf)
print(f"{len(entries)} words, {sum(1 for _, (p, o) in entries.items() if o)} offensive, {len(buf)} bytes", file=sys.stderr)
