"""Safe in-place save of an FM24 .fm archive.

Policy (Save Changes):
  1. Build the new archive in '<save>.fm.tmp' (same folder) and verify it.
  2. Copy the existing file to verified '.bk1.tmp' (+ '.bk2.tmp' on a first save).
  3. os.replace the verified temp over the original (atomic, same path, same name).
  4. Only then rotate (renames): '<save>.fm.bk1' = the file as it was just before this save,
     '<save>.fm.bk2' = the previous bk1. First save (no bk1 yet): bk1 AND bk2 are both copies
     of the original, so the pristine original survives until the third save.
Any failure before step 3 leaves the original and both backups untouched and removes temps.
The disk signature is re-checked before the backups and again right before step 3.

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


def _rm_quiet(path):
    """Cleanup that must never mask the real error."""
    try:
        _rm(path)
    except OSError:
        pass


def backup_state(path):
    """Return (first_save, previous_bk1_path_or_None). first_save = NO backup exists (no bk1, old-style
    bk1-<name>.fm or bk2). A lone bk2 (bk1 deleted) is the pristine original: never treat it as a first save."""
    bk1, bk2 = backup_paths(path)
    legacy = legacy_bk1_path(path)
    prev = bk1 if os.path.isfile(bk1) else (legacy if os.path.isfile(legacy) else None)
    return prev is None and not os.path.isfile(bk2), prev


def prepare_backups(path, progress_cb=None):
    """Create the verified backup copies as '.tmp' files; nothing existing is touched.
    Returns a state for commit_backups()/discard_backups()."""
    bk1, bk2 = backup_paths(path)
    first, prev = backup_state(path)
    st = {'path': path, 'first': first, 'prev': prev, 'tmp1': bk1 + '.tmp', 'tmp2': None}
    try:
        if progress_cb:
            progress_cb('Backing up current file (bk1)...')
        digest = _copy_verified(path, st['tmp1'])
        if first or (prev is not None and prev != bk1):  # first save, or an old-style bk1-<name>.fm: copy for bk2
            if progress_cb:
                progress_cb('Backing up (bk2)...')
            st['tmp2'] = bk2 + '.tmp'
            src, exp = (st['tmp1'], digest) if first else (prev, None)
            _copy_verified(src, st['tmp2'], exp)
    except BaseException:
        discard_backups(st)
        raise
    return st


def discard_backups(st):
    _rm_quiet(st['tmp1'])
    if st['tmp2']:
        _rm_quiet(st['tmp2'])


def commit_backups(st):
    """Rename-only rotation; call AFTER the save was replaced, so a failed replace never
    costs the older backup. Returns {'first': bool}."""
    bk1, bk2 = backup_paths(st['path'])
    if st['tmp2']:
        os.replace(st['tmp2'], bk2)
    elif st['prev'] == bk1:
        os.replace(bk1, bk2)  # previous bk1 becomes bk2
    # else: bk1 was deleted but bk2 (the original) exists: keep bk2 as it is
    os.replace(st['tmp1'], bk1)
    _fsync_dir(os.path.dirname(st['path']))
    return {'first': st['first']}


def make_backups(path, progress_cb=None):
    """Create/rotate the two backups of `path` (see module docstring). Returns {'first': bool}."""
    st = prepare_backups(path, progress_cb)
    try:
        return commit_backups(st)
    except BaseException:
        discard_backups(st)
        raise


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

    path = os.path.realpath(path)  # keep a symlinked save a symlink (replace the target)
    if not os.path.isfile(path):
        raise SaveError('The save file no longer exists on disk')
    sig = save_data.get('disk_sig')
    if sig is None:  # no load-time baseline: guard at least against changes during this save
        sig = file_signature(path)
    elif sig != file_signature(path):
        raise SaveError('The save file changed on disk since it was loaded (did FM24 or another '
                        'tool overwrite it?). Nothing was written. Reload to pick up that file; '
                        'unsaved edits would need to be redone.')

    def recheck():
        if file_signature(path) != sig:
            raise SaveError('The save file changed on disk while saving. Nothing was replaced.')
    size = os.path.getsize(path)
    first, prev = backup_state(path)
    copies = 3 if first or (prev is not None and prev != backup_paths(path)[0]) else 2
    # tmp + bk1.tmp (+ bk2.tmp on a first save or from a legacy bk1-<name>.fm); +16 MB headroom
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
        recheck()
        bst = prepare_backups(path, lambda m: emit(m, 90))
        try:
            recheck()
            emit('Replacing save file...', 97)
            os.replace(tmp, path)
        except BaseException:
            discard_backups(bst)
            raise
    except BaseException:
        _rm(tmp)
        raise
    try:
        info = commit_backups(bst)
    except OSError as e:  # the save itself is already in place: report, do not claim it failed
        discard_backups(bst)
        info = {'first': bst['first'], 'backup_error': str(e)}
    _fsync_dir(os.path.dirname(path))

    header, nmembers, marker, aname, sdc, subdirs = parse_archive(path)
    save_data.update(header=header, members=nmembers, index_marker=marker, archive_name=aname,
                     subdir_count=sdc, subdirs=subdirs, disk_sig=file_signature(path))
    info['bk1'], info['bk2'] = backup_paths(path)
    emit('Done.', 100)
    return info
