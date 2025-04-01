# import firebase_admin
# from firebase_admin import credentials, firestore, storage

# # cred = credentials.Certificate("app/firebase/firebaseCredentialsKey.json")
# # firebase_admin.initialize_app(cred, {
# #     'storageBucket': 'reqpal-2025.appspot.com'
# # })

# # db = firestore.client()
# # bucket = storage.bucket()

# if not firebase_admin._apps:
#     cred = credentials.Certificate("app/firebase/firebaseCredentialsKey.json")
#     firebase_admin.initialize_app(cred, {
#         'storageBucket': 'reqpal.appspot.com'
#     })

# db = firestore.client()
# bucket = storage.bucket()

# print("✅ Connected to bucket:", bucket.name)