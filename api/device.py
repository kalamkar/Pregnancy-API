'''
Created on Sep 25, 2014

@author: abhijit
'''

import api
import webapp2

from datastore import Device

class DeviceAPI(webapp2.RequestHandler):

    def post(self):
        uuid = self.request.get('id')
        device_type = self.request.get('type')
        push_token = self.request.get('token')
        model = self.request.get('model')

        if not uuid:
            api.write_error(self.response, 400, 'Missing required parameter')
            return

        query = Device.query(Device.uuid == uuid)
        if query.count() > 0:
            device = query.get()
        else:
            device = Device(uuid=uuid)

        try:
            if push_token and device_type:
                device.push_token = push_token
                device.device_type = device_type.upper()
        except:
            api.write_error(self.response, 400, 'Invalid token or device type')
            return

        device.model = model

        device.put_async()

        api.write_message(self.response, 'Updated device')

    def put(self):
        self.post()

    def get(self):
        uuid = self.request.get('id')
        if not uuid:
            api.write_error(self.response, 400, 'Missing required parameter')
            return

        device = Device.query(Device.uuid == uuid).get()
        device_json = {'uuid': device.uuid, 'type': device.device_type, 'token': device.push_token,
                       'update_time': device.update_time.isoformat(' '),
                       'create_time': device.create_time.isoformat(' '), }

        api.write_message(self.response, 'success', extra={'device' : device_json})
