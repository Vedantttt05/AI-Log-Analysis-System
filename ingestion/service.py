"""Persist parsed entries and upload summary using existing SQLite operations."""
from database.models import UploadedFile
from database.operations import add_log

def import_records(session, filename, records, errors=None):
    created = 0
    for record in records:
        _, inserted = add_log(session, **record)
        created += int(inserted)
    upload = UploadedFile(filename=filename, file_type=filename.rsplit(".", 1)[-1].lower(),
                          total_records=len(records), status="Imported" if records else "No valid records")
    session.add(upload)
    session.flush()
    return {"created": created, "duplicates": len(records) - created,
            "malformed": len(errors or []), "upload_id": upload.id}
