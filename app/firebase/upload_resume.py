# from app.firebase.client import bucket

# def upload_to_storage_if_not_exists(path: str, content: bytes):
#     blob = bucket.blob(path)
#     if not blob.exists():
#         blob.upload_from_string(content)