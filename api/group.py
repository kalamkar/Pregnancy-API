'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

import api
import config
import cloudstorage as gcs
import logging
import StringIO
import webapp2
import uuid

from PIL import Image, ImageDraw
from google.appengine.api import images as ImageApi
from google.appengine.ext import blobstore

from datastore import Group
from datastore import User

from api.renderer import get_group_json

from google.appengine.ext import ndb
from api.search import update_index

class GroupAPI(webapp2.RequestHandler):

    def post(self):
        if self.request.get('_put'):
            self.put()
            return

        name = self.request.get('name')
        member_ids = self.request.get_all('member_uuid')
        public = self.request.get('public')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        group = Group(uuid=str(uuid.uuid4()))
        group.admins.append(user.key)
        group.members.append(user.key)
        group.name = name
        if 'public' in self.request.params and not public == '':
            group.public = public.lower() in ("yes", "true", "t", "1", "on")
        for member_id in member_ids:
            member = User.query(User.uuid == member_id).get()
            if member:
                group.members.append(member.key)
        group.put()
        update_index(group)

        api.write_message(self.response, 'success', extra={'groups' : [ get_group_json(group) ]})

    def put(self):
        uuid = self.request.get('group_uuid')
        name = self.request.get('name')
        admin_ids = self.request.get_all('admin_uuid')
        member_ids = self.request.get_all('member_uuid')
        public = self.request.get('public')

        if not uuid:
            api.write_error(self.response, 400, 'Missing required parameter, group_uuid')
            return

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 403, 'Unknown or missing user')
            return

        group = Group.query(Group.uuid == uuid).get()
        if not group:
            api.write_error(self.response, 404, 'Unknown or missing group')
            return

        if not user.key in group.admins:
            api.write_error(self.response, 403, 'User not allowed to update group')
            return

        if name:
            group.name = name
        if 'public' in self.request.params and not public == '':
            group.public = public.lower() in ("yes", "true", "t", "1", "on")

        for admin_id in admin_ids:
            remove_user = False
            if admin_id and admin_id[0] == '-':
                remove_user = True
                admin_id = admin_id[1:]
            admin = User.query(User.uuid == admin_id).get()
            if admin:
                if remove_user and admin.key in group.admins:
                    if len(group.admins) > 1:
                        group.admins.remove(admin.key)
                    else:
                        api.write_error(self.response, 403, 'Cannot remove last admin')
                        return
                elif not admin.key in group.admins:
                    group.admins.append(admin.key)
            else:
                logging.warn('Unknown user %s' % (admin_id))

        for member_id in member_ids:
            remove_user = False
            if member_id and member_id[0] == '-':
                remove_user = True
                member_id = member_id[1:]
            member = User.query(User.uuid == member_id).get()
            if member:
                if remove_user and member.key in group.members:
                    group.members.remove(member.key)
                elif not member.key in group.members:
                    group.members.append(member.key)
            else:
                logging.warn('Unknown user %s' % (member_id))
        group.put()
        update_index(group)

        api.write_message(self.response, 'Updated group',
                          extra={'groups' : [ get_group_json(group) ]})


    def get(self):
        uuid = self.request.get('group_uuid')

        user = api.get_user(self.request)
        if not user:
            api.write_error(self.response, 403, 'Unknown or missing user')
            return

        if uuid:
            query = Group.query(Group.uuid == uuid)
        else:
            query = Group.query(ndb.OR(Group.members == user.key,
                                       Group.admins == user.key)).order(-Group.update_time)

        groups = []
        for group in query:
            if user.key in group.members or user.key in group.admins:
                groups.append(get_group_json(group))

        api.write_message(self.response, 'success', extra={'groups' : groups})


class GroupPhotoAPI(webapp2.RequestHandler):
    def get(self):
        uuid = self.request.get('group_uuid')
        size = self.request.get('size')
        size = int(size) if size else config.PROFILE_ICON_SIZE

        if not uuid:
            api.write_error(self.response, 400, 'Unknown or missing user')
            return

        group = Group.query(Group.uuid == uuid).get()
        if not group:
            api.write_error(self.response, 404, 'Unknown or missing group')
            return

        images = []
        positions = [(0, 0), (size / 2, 0), (size / 2, size / 2)]

        for member_key in group.members:
            if len(images) == len(positions):
                break
            member = member_key.get()
            if not member:
                continue

            filename = config.PROFILE_BUCKET + member.uuid
            image = ImageApi.Image(blob_key=blobstore.create_gs_key('/gs' + filename))
            try:
                gcs_file = gcs.open(filename, 'r')
                images.append(image)
            except:
                pass

        if len(images) == 0:
            api.write_error(self.response, 404, 'No group photo available')
            return
        elif len(images) == 1:
            sizes = [(size, size)]
        elif len(images) == 2:
            sizes = [(size / 2, size), (size / 2, size)]
        else:
            sizes = [(size / 2, size), (size / 2, size / 2), (size / 2, size / 2)]

        new_im = Image.new('RGB', (size, size), color=(255, 255, 255, 0))
        for image in images:
            (width, height) = sizes.pop(0)
            image.resize(width=width, height=height, crop_to_fit=True, allow_stretch=False)
            im = Image.open(StringIO.StringIO(image.execute_transforms(output_encoding=ImageApi.PNG)))
            new_im.paste(im, positions.pop(0))

        bigsize = (new_im.size[0] * 3, new_im.size[1] * 3)
        mask = Image.new('L', bigsize, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(new_im.size, Image.ANTIALIAS)
        new_im.putalpha(mask)

        output = StringIO.StringIO()
        new_im.save(output, 'PNG')

        self.response.headers['Content-Type'] = 'image/png'
        self.response.headers['Cache-Control'] = 'public,max-age=%d' % (config.MEDIA_MAX_AGE)
        self.response.out.write(output.getvalue())
        output.close()
