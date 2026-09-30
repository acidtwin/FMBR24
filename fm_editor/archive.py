"""FMF archive read/write - zstd-compressed member container."""
import struct, io, os
import zstandard as zstd


def _rfile(path, offset, length):
    with open(path, 'rb') as f:
        f.seek(offset)
        return f.read(length)


def _decomp(data, limit=2 * 1024 ** 3):
    return zstd.ZstdDecompressor().decompress(data, max_output_size=limit)


def _comp(data):
    return zstd.ZstdCompressor(level=3).compress(bytes(data))


def _u32(b, p): return struct.unpack_from('<I', b, p)[0]
def _u64(b, p): return struct.unpack_from('<Q', b, p)[0]


def parse_archive(path):
    """Return (header, members, index_marker, archive_name, subdir_count, subdirs)."""
    h = bytearray(_rfile(path, 0, 26))
    if h[:6] != b'\x02\x01fmf.':
        raise ValueError("Not an FM save file (bad magic bytes)")
    idx_ptr = _u64(h, 9)
    start = idx_ptr + 9
    file_size = os.path.getsize(path)
    index_marker = _rfile(path, start, 9)
    compressed_idx = _rfile(path, start + 9, file_size - start - 9)
    idx = _decomp(compressed_idx, 64 * 1024 ** 2)

    pos = 0
    def rs():
        nonlocal pos
        n = _u32(idx, pos); pos += 4
        s = idx[pos:pos + n].decode('utf-8', errors='replace'); pos += n
        return s
    def ru32():
        nonlocal pos; v = _u32(idx, pos); pos += 4; return v
    def ru64():
        nonlocal pos; v = _u64(idx, pos); pos += 8; return v

    members = []
    def read_group(group):
        nonlocal pos
        for _ in range(ru32()):
            parts = []
            for _ in range(20):
                part = rs(); parts.append(part)
                if part.startswith('.'): break
            name = group + ''.join(parts)
            o = ru64(); s = ru64(); p = ru64()
            unk16 = bytes(idx[pos:pos + 16]); pos += 16
            members.append({'name': name, 'o': o, 's': s, 'p': p,
                            'parts': parts, 'unk16': unk16, 'group': group})

    archive_name = rs()
    read_group('')
    subdir_count = ru32()
    subdirs = []
    for _ in range(subdir_count):
        dname = rs(); subdirs.append(dname)
        read_group(dname + '/')

    return h, members, index_marker, archive_name, subdir_count, subdirs


def get_member_raw(path, m):
    return _rfile(path, m['o'] + 26, m['s'])


def get_member(path, m):
    data = _decomp(get_member_raw(path, m), m['p'])
    assert len(data) == m['p']
    return bytearray(data)


def _serialize_index(archive_name, members, subdir_count, subdirs, updated):
    buf = io.BytesIO()
    def ws(s):
        b = s.encode('utf-8')
        buf.write(struct.pack('<I', len(b))); buf.write(b)
    def wu32(v): buf.write(struct.pack('<I', v))
    def wu64(v): buf.write(struct.pack('<Q', v))

    ws(archive_name)
    root = [m for m in members if m['group'] == '']
    wu32(len(root))
    for m in root:
        for part in m['parts']: ws(part)
        u = updated[m['name']]
        wu64(u['o']); wu64(u['s']); wu64(u['p'])
        buf.write(m['unk16'])

    wu32(subdir_count)
    for dname in subdirs:
        ws(dname)
        sub = [m for m in members if m['group'] == dname + '/']
        wu32(len(sub))
        for m in sub:
            for part in m['parts']: ws(part)
            u = updated[m['name']]
            wu64(u['o']); wu64(u['s']); wu64(u['p'])
            buf.write(m['unk16'])

    buf.write(b'\x00\x00\x00\x00')  # required index terminator
    return buf.getvalue()


def write_archive(output_path, orig_path, header, members, index_marker,
                  archive_name, subdir_count, subdirs, patched_members,
                  progress_cb=None):
    """
    patched_members: dict of member name -> bytearray with new content.
    progress_cb: optional callable(message: str, pct: int).
    """
    def emit(msg, pct):
        if progress_cb:
            progress_cb(msg, pct)

    n = len(members)
    emit("Recompressing modified member(s)...", 10)
    member_data = {}
    for i, m in enumerate(members):
        name = m['name']
        if name in patched_members:
            emit(f"Compressing {name}...", 10 + 50 * i // max(n, 1))
            member_data[name] = _comp(patched_members[name])
        else:
            member_data[name] = get_member_raw(orig_path, m)

    emit("Recompression done.", 60)

    updated = {}
    current = 0
    for m in members:
        name = m['name']
        s_new = len(member_data[name])
        updated[name] = {'o': current, 's': s_new, 'p': m['p']}
        current += s_new

    start_new = 26 + current
    idx_ptr_new = start_new - 9

    emit("Building index...", 65)
    new_idx_bytes = _serialize_index(archive_name, members, subdir_count, subdirs, updated)
    compressed_idx = _comp(new_idx_bytes)

    new_marker = bytearray(index_marker)
    if index_marker[0] == 3:
        struct.pack_into('<Q', new_marker, 1, len(new_idx_bytes))

    new_header = bytearray(header)
    struct.pack_into('<Q', new_header, 9, idx_ptr_new)

    emit(f"Writing {os.path.basename(output_path)}...", 75)
    with open(output_path, 'wb') as f:
        f.write(new_header)
        for m in members:
            f.write(member_data[m['name']])
        f.write(new_marker)
        f.write(compressed_idx)
        f.flush()
        os.fsync(f.fileno())  # durable before the caller swaps it over the original

    emit(f"Done. {os.path.getsize(output_path) // 1024 // 1024} MB written.", 100)
