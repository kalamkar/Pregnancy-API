'''
Created on Sep 25, 2014

@author: abhi@dovetail.care (Abhijit Kalamkar)
'''

from api import get_time_millis


def get_user_json(user, public=True):
    json = {'uuid': user.uuid, 'name': user.name,
            'update_time': get_time_millis(user.update_time),
            'create_time': get_time_millis(user.create_time)}
    if user.last_location and user.last_location.name:
        json['location'] = user.last_location.name

    if not public:
        email = None
        if user.devices:
            for device in user.devices:
                if device.data and device.device_type == 'EMAIL':
                    email = device.data
        json['email'] = email
        json['auth'] = user.auth
        features = {}
        for feature in user.features:
            if feature.name and not feature.name[0] == '_':
                features[feature.name] = feature.value
        json['features'] = features
        insights = []
        for insight in user.insights:
            insights.append({'title': insight.title, 'tags': insight.tags.split(','),
                             'priority': insight.priority})
        json['insights'] = insights
    return json


def get_message_json(message):
    return {'sender': get_user_json(message.sender.get()), 'text': message.text,
            'group_uuid': message.key.parent().get().uuid,
            'create_time': get_time_millis(message.create_time)}



def get_group_json(group):
    admins = []
    members = []

    for admin in group.admins:
        admins.append(get_user_json(admin.get()))

    for member_key in group.members:
        member = member_key.get()
        if member:
            members.append(get_user_json(member))

    json = {'uuid': group.uuid, 'name': group.name, 'admins': admins, 'members': members,
            'public': group.public,
            'update_time': get_time_millis(group.update_time),
            'create_time': get_time_millis(group.create_time)}
    return json


def get_event_json(event):
    json = {'type': event.event_type, 'time': get_time_millis(event.time), 'data': event.data}
    return json


def get_appointment_json(appointment, provider):
    json = {'id': appointment.key.urlsafe(),
            'time': get_time_millis(appointment.time),
            'minutes': appointment.minutes,
            'update_time': get_time_millis(appointment.update_time),
            'create_time': get_time_millis(appointment.create_time)}
    if appointment.consumer:
        json['consumer'] = get_user_json(appointment.consumer.get())
    if provider:
        json['provider'] = get_user_json(provider)
    return json

