"""Safe in-place save of an FM24 .fm archive.

Policy (Save Changes):
  1. Build the new archive in '<save>.fm.tmp' (same folder) and verify it.
  2. Back up the existing file: '<save>.fm.bk1' = the file as it was just before this save,
     '<save>.fm.bk2' = the previous bk1. First save (no bk1 yet): bk1 AND bk2 are both copies
     of the original, so the pristine original survives until the third save.
  3. os.replace the verified temp over the original (atomic, same path, same name).
Any failure before step 3 leaves the original untouched and removes the temp file.

Backups end in '.bk1'/'.bk2' (not '.fm') so FM24's Load Game screen does not list them.
To use one in FM24, copy it next to the saves and drop the '.bk1' suffix. Old-style
'bk1-<name>.fm' files from earlier versions are recognised as the previous bk1 and left alone.
"""
import hashlib
import os
import shutil

from fm_editor.archive import write_archive, parse_archive, get_member_raw, get_member

_CHUNK = 8 * 1024 * 1024


class SaveError(Exception):
    pass


def backup_paths(path):
    return path + '.bk1', path + '.bk2'


def legacy_bk1_path(path):
    d, n = os.path.split(path)
    return os.path.join(d, 'bk1-' + n)


def file_signature(path):
    st = os.stat(path)
    return (st.st_size, st.st_mtime_ns)


def _sha(data):
    return hashlib.sha256(data).digest()


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            c = f.read(_CHUNK)
            if not c:
                return h.digest()
            h.update(c)


def _copy_verified(src, dst_tmp, expected=None):
    """Copy src -> dst_tmp (fsynced), then re-read dst_tmp and check size + sha256. Return digest."""
    h = hashlib.sha256()
    n = 0
    with open(src, 'rb') as fi, open(dst_tmp, 'wb') as fo:
        while True:
            c = fi.read(_CHUNK)
            if not c:
                break
            h.update(c)
            fo.write(c)
            n += len(c)
        fo.flush()
        os.fsync(fo.fileno())
    digest = h.digest()
    if expected is not None and digest != expected:
        raise SaveError(f'{os.path.basename(src)} changed while being backed up')
    if os.path.getsize(dst_tmp) != n or _sha_file(dst_tmp) != digest:
        raise SaveError(f'Backup verification failed for {os.path.basename(dst_tmp)}')
    return digest


def _fsync_dir(folder):
    try:
        fd = os.open(folder, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass  # best effort (not every filesystem allows it)


def _rm(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def backup_state(path):
    """Return (first_save, previous_bk1_path_or_None). first_save = no bk1 (new or legacy) exists."""
    bk1, _ = backup_paths(path)
    legacy = legacy_bk1_path(path)
    prev = bk1 if os.path.isfile(bk1) else (legacy if os.path.isfile(legacy) else None)
    return prev is None, prev


def make_backups(path, progress_cb=None):
    """Create/rotate the two backups of `path` (see module docstring). Returns {'first': bool}."""
    bk1, bk2 = backup_paths(path)
    first, prev = backup_state(path)
    tmp1, tmp2 = bk1 + '.tmp', bk2 + '.tmp'
    try:
        if progress_cb:
            progress_cb('Backing up current file (bk1)...')
        digest = _copy_verified(path, tmp1)
        if prev == bk1:
            os.replace(bk1, bk2)  # rotate: previous bk1 becomes bk2 (rename, no copy)
        else:  # first save, or only an old-style bk1-<name>.fm exists: copy
            if progress_cb:
                progress_cb('Backing up (bk2)...')
            src, exp = (tmp1, digest) if first else (prev, None)
            _copy_verified(src, tmp2, exp)
            os.replace(tmp2, bk2)
        os.replace(tmp1, bk1)
    except BaseException:
        _rm(tmp1)
        _rm(tmp2)
        raise
    _fsync_dir(os.path.dirname(path))
    return {'first': first}


def verify_archive(tmp_path, orig_path, old_members, new_gdb):
    """Re-open the freshly written archive and check it against the original + the new game_db."""
    _h, nmembers, _m, _a, _c, _s = parse_archive(tmp_path)
    if [m['name'] for m in nmembers] != [m['name'] for m in old_members]:
        raise SaveError('Verification failed: member list differs')
    for nm, om in zip(nmembers, old_members):
        if nm['name'] == 'game_db.dat':
            if nm['p'] != len(new_gdb):
                raise SaveError('Verification failed: game_db.dat length')
            if _sha(get_member(tmp_path, nm)) != _sha(new_gdb):
                raise SaveError('Verification failed: patched game_db.dat content')
        else:
            if (nm['p'], nm['unk16']) != (om['p'], om['unk16']) or \
               _sha(get_member_raw(tmp_path, nm)) != _sha(get_member_raw(orig_path, om)):
                raise SaveError(f"Verification failed: member {nm['name']} differs")


def save_in_place(save_data, path, progress_cb=None):
    """Write save_data['b'] back to `path` with verified temp file + 2 rotating backups.

    progress_cb(msg, pct). On success updates save_data's archive layout (members/header/...)
    and disk_sig to describe the new file and returns {'first': bool, 'bk1': p, 'bk2': p}.
    On failure raises and leaves the original untouched.
    """
    def emit(msg, pct):
        if progress_cb:
            progress_cb(msg, pct)

    if not os.path.isfile(path):
        raise SaveError('The save file no longer exists on disk')
    sig = save_data.get('disk_sig')
    if sig is not None and sig != file_signature(path):
        raise SaveError('The save file changed on disk since it was loaded (did FM24 or another '
                        'tool overwrite it?). Nothing was written. Reload to pick up that file; '
                        'unsaved edits would need to be redone.')
    size = os.path.getsize(path)
    first, _prev = backup_state(path)
    copies = 3 if first else 2  # tmp + bk1.tmp (+ bk2.tmp on first save); +16 MB headroom
    free = shutil.disk_usage(os.path.dirname(path)).free
    if free < copies * size + 16 * 1024 * 1024:
        raise SaveError(f'Not enough free disk space: need about {copies * size // 1024 ** 2} MB '
                        f'free next to the save, have {free // 1024 ** 2} MB. Nothing was written.')

    b = save_data['b']
    members = [dict(m) for m in save_data['members']]  # copies: a failed save must not mutate state
    gdb = next((m for m in members if m['name'] == 'game_db.dat'), None)
    if gdb is None:
        raise SaveError('game_db.dat member not found in archive')
    gdb['p'] = len(b)

    tmp = path + '.tmp'
    _rm(tmp)
    try:
        write_archive(tmp, path, save_data['header'], members, save_data['index_marker'],
                      save_data['archive_name'], save_data['subdir_count'], save_data['subdirs'],
                      {'game_db.dat': b},
                      progress_cb=lambda m, p: emit(m, 2 + p * 70 // 100))
        emit('Verifying new file...', 74)
        verify_archive(tmp, path, members, b)
        shutil.copymode(path, tmp)
        emit('Creating backups...', 86)
        info = make_backups(path, lambda m: emit(m, 90))
        emit('Replacing save file...', 97)
        os.replace(tmp, path)
    except BaseException:
        _rm(tmp)
        raise
    _fsync_dir(os.path.dirname(path))

    header, nmembers, marker, aname, sdc, subdirs = parse_archive(path)
    save_data.update(header=header, members=nmembers, index_marker=marker, archive_name=aname,
                     subdir_count=sdc, subdirs=subdirs, disk_sig=file_signature(path))
    info['bk1'], info['bk2'] = backup_paths(path)
    emit('Done.', 100)
    return info
