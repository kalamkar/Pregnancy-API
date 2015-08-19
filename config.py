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

APNS_DEV = ('gateway.sandbox.push.apple.com', 2195)
APNS = ('gateway.push.apple.com', 2195)
GCM_URL = 'https://android.googleapis.com/gcm/send'

GCM_API_KEY = 'AIzaSyBOrPebHVw-4vTWjcgXOVPQUjAOajCeXEw'
