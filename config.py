'''
Created on Jun 8, 2015

@author: abhijit kalamkar
'''

STORAGE_URL = 'http://commondatastorage.googleapis.com'
IMAGES_BUCKET = '/dovetail-images/'
PROFILE_BUCKET = '/dovetail-profiles/'
MEDIA_MAX_AGE = 30 * 24 * 60 * 60
DEFAULT_PHOTO_URL = 'https://storage.googleapis.com' + PROFILE_BUCKET + 'ic_user.png'
PROFILE_ICON_SIZE = 50

CHART_MAX_AGE = 1 * 24 * 60 * 60

SUPER_USER_UUID = 'da41806f-8761-4007-b675-352a9e46ce8a'
SUPER_USER_AUTH = 'ee2ccf02-3e51-4a08-9609-7637539388ee'

APNS_DEV = ('gateway.sandbox.push.apple.com', 2195)
APNS = ('gateway.push.apple.com', 2195)
GCM_URL = 'https://android.googleapis.com/gcm/send'

GCM_API_KEY = 'AIzaSyBOrPebHVw-4vTWjcgXOVPQUjAOajCeXEw'
