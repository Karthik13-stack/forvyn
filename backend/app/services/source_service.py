from pathlib import Path
import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import UploadFile

APP_DIR = Path(__file__).resolve().parents[1]
SOURCES_DIR = APP_DIR / 'storage' / 'sources'
METADATA_FILE = SOURCES_DIR / 'metadata.json'
SOURCES_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify_filename(filename: str) -> str:
    clean = Path(filename).name
    clean = re.sub(r'[^A-Za-z0-9._-]+', '_', clean).strip('._-')
    return clean or f'source_{uuid.uuid4().hex[:8]}'


def _load_metadata() -> List[Dict]:
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, 'r', encoding='utf-8') as handle:
                data = json.load(handle)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def _save_metadata(records: List[Dict]) -> None:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, 'w', encoding='utf-8') as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)


def _find_record(name: str) -> Optional[Dict]:
    for record in _load_metadata():
        if record.get('stored_name') == name or record.get('original_name') == name:
            return record
    return None


def _file_record(path: Path) -> Dict:
    now = _now()
    return {
        'id': uuid.uuid4().hex,
        'original_name': path.name,
        'stored_name': path.name,
        'category': '',
        'notes': '',
        'source_type': '',
        'size_bytes': path.stat().st_size if path.exists() else 0,
        'created_at': now,
        'updated_at': now,
        'exists': path.exists(),
    }

def save_source(upload_filename: str, fileobj, *, category: str = '', notes: str = '', source_type: str = '') -> Dict:
    stored_name = f"{uuid.uuid4().hex[:10]}_{_slugify_filename(upload_filename)}"
    dest = SOURCES_DIR / stored_name
    with open(dest, 'wb') as f:
        shutil.copyfileobj(fileobj, f)
    size_bytes = dest.stat().st_size if dest.exists() else 0
    record = {
        'id': uuid.uuid4().hex,
        'original_name': Path(upload_filename).name,
        'stored_name': dest.name,
        'category': category.strip(),
        'notes': notes.strip(),
        'source_type': source_type.strip(),
        'size_bytes': size_bytes,
        'created_at': _now(),
        'updated_at': _now(),
    }
    records = _load_metadata()
    records = [item for item in records if item.get('stored_name') != record['stored_name']]
    records.insert(0, record)
    _save_metadata(records)
    return record

def list_sources() -> List[Dict]:
    records = _load_metadata()
    records_by_name = {item.get('stored_name'): item for item in records}
    sources = []
    for path in sorted(SOURCES_DIR.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file() or path.name == METADATA_FILE.name:
            continue
        record = records_by_name.get(path.name)
        if not record:
            record = {
                'id': uuid.uuid4().hex,
                'original_name': path.name,
                'stored_name': path.name,
                'category': '',
                'notes': '',
                'source_type': '',
                'size_bytes': path.stat().st_size,
                'created_at': _now(),
                'updated_at': _now(),
            }
        record = dict(record)
        record['size_bytes'] = path.stat().st_size
        sources.append(record)
    sources.sort(key=lambda item: item.get('created_at', ''), reverse=True)
    return sources


def search_sources(query: str) -> List[Dict]:
    q = query.strip().lower()
    if not q:
        return list_sources()
    results = []
    for record in list_sources():
        haystack = ' '.join([
            record.get('original_name', ''),
            record.get('stored_name', ''),
            record.get('category', ''),
            record.get('notes', ''),
            record.get('source_type', ''),
        ]).lower()
        if q in haystack:
            results.append(record)
    return results

def update_source_metadata(name: str, *, category: Optional[str] = None, notes: Optional[str] = None, source_type: Optional[str] = None) -> Optional[Dict]:
    records = _load_metadata()
    updated = None
    for record in records:
        if record.get('stored_name') == name or record.get('original_name') == name:
            if category is not None:
                record['category'] = category.strip()
            if notes is not None:
                record['notes'] = notes.strip()
            if source_type is not None:
                record['source_type'] = source_type.strip()
            record['updated_at'] = _now()
            updated = record
            break
    if updated is None:
        path = SOURCES_DIR / name
        if path.exists() and path.is_file():
            updated = _file_record(path)
            if category is not None:
                updated['category'] = category.strip()
            if notes is not None:
                updated['notes'] = notes.strip()
            if source_type is not None:
                updated['source_type'] = source_type.strip()
            records.insert(0, updated)
    if updated:
        _save_metadata(records)
    return updated


def delete_source(name: str) -> bool:
    record = _find_record(name)
    stored_name = record.get('stored_name') if record else name
    p = SOURCES_DIR / stored_name
    if p.exists() and p.is_file():
        p.unlink()
        records = [item for item in _load_metadata() if item.get('stored_name') != stored_name and item.get('original_name') != name]
        _save_metadata(records)
        return True
    return False

def get_source_path(name: str) -> str:
    record = _find_record(name)
    stored_name = record.get('stored_name') if record else name
    p = SOURCES_DIR / stored_name
    return str(p) if p.exists() and p.is_file() else ''


def get_source(name: str) -> Dict:
    record = _find_record(name)
    if not record:
        path = SOURCES_DIR / name
        if path.exists() and path.is_file():
            return _file_record(path)
        return {}
    path = SOURCES_DIR / record['stored_name']
    record = dict(record)
    record['size_bytes'] = path.stat().st_size if path.exists() else record.get('size_bytes', 0)
    record['exists'] = path.exists()
    return record