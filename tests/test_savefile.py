"""Plain script: python3 tests/test_savefile.py  (prints OK). Uses a small synthetic .fm archive
in a temp dir; never touches real saves."""
import os
import struct
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fm_editor import archive as A
from fm_editor import savefile as S


def build_archive(path, contents):
    """Write a minimal valid .fm: contents = {member_name: bytes}; root group only."""
    members, blobs, cur = [], [], 0
    for name, data in contents.items():
        stem, ext = name.rsplit('.', 1)
        comp = A._comp(data)
        members.append({'name': name, 'parts': [stem, '.' + ext], 'group': '', 'unk16': bytes(range(16)),
                        'o': cur, 's': len(comp), 'p': len(data)})
        blobs.append(comp)
        cur += len(comp)
    updated = {m['name']: m for m in members}
    idx = A._serialize_index('test.fm', members, 0, [], updated)
    marker = bytearray(9)
    marker[0] = 3
    struct.pack_into('<Q', marker, 1, len(idx))
    header = bytearray(26)
    header[:6] = b'\x02\x01fmf.'
    struct.pack_into('<Q', header, 9, 26 + cur - 9)
    with open(path, 'wb') as f:
        f.write(header)
        for bl in blobs:
            f.write(bl)
        f.write(marker)
        f.write(A._comp(idx))


def load(path):
    header, members, marker, aname, sdc, subdirs = A.parse_archive(path)
    g = next(m for m in members if m['name'] == 'game_db.dat')
    return {'b': A.get_member(path, g), 'header': header, 'members': members, 'index_marker': marker,
            'archive_name': aname, 'subdir_count': sdc, 'subdirs': subdirs,
            'disk_sig': S.file_signature(path)}


def rd(p):
    with open(p, 'rb') as f:
        return f.read()


def main():
    base = {'game_db.dat': os.urandom(200_000) + b'\x00' * 50_000, 'other.bin': os.urandom(30_000),
            'small.txt': b'hello'}
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'Save.fm')
        build_archive(path, base)
        orig = rd(path)
        bk1, bk2 = S.backup_paths(path)
        assert bk1.endswith('.fm.bk1') and not bk1.endswith('.fm')  # FM24 will not list it

        # 1. first save: bk1 and bk2 both equal the original; patched byte present after re-parse
        sd = load(path)
        sd['b'][1234] ^= 0xFF
        patched1 = bytes(sd['b'])
        info = S.save_in_place(sd, path)
        assert info['first'] is True
        assert rd(bk1) == orig and rd(bk2) == orig
        assert rd(path) != orig
        sd2 = load(path)
        assert bytes(sd2['b']) == patched1
        assert A.get_member(path, next(m for m in sd2['members'] if m['name'] == 'other.bin')) == \
            bytearray(base['other.bin'])
        assert not os.path.exists(path + '.tmp') and not os.path.exists(bk1 + '.tmp')
        # save_data layout was refreshed, so a second save reads the right offsets
        assert sd['members'] == sd2['members'] and sd['disk_sig'] == S.file_signature(path)

        # 2. second save (reusing the same in-memory state): rotate. bk2 = 1st-save file, bk1 = same-as-before
        after1 = rd(path)
        sd['b'][99] ^= 0x55
        patched2 = bytes(sd['b'])
        info = S.save_in_place(sd, path)
        assert info['first'] is False
        assert rd(bk1) == after1 and rd(bk2) == orig, 'bk2 must be previous bk1'
        assert bytes(load(path)['b']) == patched2
        after2 = rd(path)

        # 3. third save: original finally rotates out
        sd['b'][5] ^= 1
        S.save_in_place(sd, path)
        assert rd(bk1) == after2 and rd(bk2) == after1

        # 4. failure injection: bad verification leaves original + backups untouched
        cur, b1, b2 = rd(path), rd(bk1), rd(bk2)
        sd['b'][7] ^= 1
        real_verify = S.verify_archive
        def bad_verify(*a, **k): raise S.SaveError('injected')
        S.verify_archive = bad_verify
        try:
            S.save_in_place(sd, path); raise AssertionError('should fail')
        except S.SaveError:
            pass
        finally:
            S.verify_archive = real_verify
        assert rd(path) == cur and rd(bk1) == b1 and rd(bk2) == b2
        assert not os.path.exists(path + '.tmp')

        # 5. exception mid-write (crash in write_archive) -> original untouched, temp removed
        real_write = S.write_archive
        def boom(out, *a, **k):
            open(out, 'wb').write(b'partial'); raise OSError('disk full (injected)')
        S.write_archive = boom
        try:
            S.save_in_place(sd, path); raise AssertionError('should fail')
        except OSError:
            pass
        finally:
            S.write_archive = real_write
        assert rd(path) == cur and not os.path.exists(path + '.tmp')

        # 6. backup copy failure -> abort before replacing the original
        real_copy = S._copy_verified
        def bad_copy(*a, **k): raise S.SaveError('injected backup failure')
        S._copy_verified = bad_copy
        try:
            S.save_in_place(sd, path); raise AssertionError('should fail')
        except S.SaveError:
            pass
        finally:
            S._copy_verified = real_copy
        assert rd(path) == cur and rd(bk1) == b1 and rd(bk2) == b2
        assert not os.path.exists(path + '.tmp') and not os.path.exists(bk1 + '.tmp')

        # 7. file changed on disk since load -> refused, nothing written
        sd['disk_sig'] = (1, 1)
        try:
            S.save_in_place(sd, path); raise AssertionError('should fail')
        except S.SaveError as e:
            assert 'changed on disk' in str(e)
        assert rd(path) == cur
        sd['disk_sig'] = S.file_signature(path)

        # 8. not enough disk space -> refused
        real_du = S.shutil.disk_usage
        S.shutil.disk_usage = lambda p: type('U', (), {'free': 10})()
        try:
            S.save_in_place(sd, path); raise AssertionError('should fail')
        except S.SaveError as e:
            assert 'free disk space' in str(e)
        finally:
            S.shutil.disk_usage = real_du
        assert rd(path) == cur

        # 9. legacy 'bk1-<name>' counts as the previous bk1 (becomes bk2), is left alone
        d2 = os.path.join(d, 'leg'); os.mkdir(d2)
        p2 = os.path.join(d2, 'L.fm')
        build_archive(p2, base)
        o2 = rd(p2)
        with open(S.legacy_bk1_path(p2), 'wb') as f:
            f.write(b'old-style backup')
        s2 = load(p2); s2['b'][3] ^= 1
        S.save_in_place(s2, p2)
        assert rd(S.backup_paths(p2)[0]) == o2 and rd(S.backup_paths(p2)[1]) == b'old-style backup'
        assert rd(S.legacy_bk1_path(p2)) == b'old-style backup'
    print('OK')


if __name__ == '__main__':
    main()
