import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder as encode
from functools import partial
from tokens import bottrix_token, test_room_token, loaned_devices_room_token


# Endpoint for webex api to send messages direct or to a room
msg_endpoint = 'https://webexapis.com/v1/messages'
headers = {  # Header for webex api, says in documentation needs a bearer token for auth
    'Authorization': bottrix_token
}

# Func to find persons webex ID using their email
# Need Person ID to send diret message
# Splits eailk into parts to just get the username
# Access a seperate endpoint the people endpoint an uses username in a querey to find personID
# Uses same global header with Bottrix's bearer token


def personId(email):
    user = email.split('@')[0]
    endpoint = f'https://webexapis.com/v1/people?email={user}%40cisco.com'
    data = requests.get(endpoint, headers=headers)
    try:
        id = data.json()['items'][0]['id']
    except IndexError:
        print(data)
        return
    return id
    ...

# Func to send a direct message to a person
# Takes message and email params
# Message param is a list with two elements the title of the message and the message body
# email param is sent to personId() to collect user's personId
# Markdown property is used to format how the messages will look leaving this function
# Uses same global header with Bottrix's bearer token


def send_direct_msg(msg, email):
    data = {
        'toPersonId': personId(email),
        'text': msg,
        'markdown': f'<blockquote class=danger> <strong>\n{msg[0]}</strong> {msg[1]} '
    }

    resp = requests.post(msg_endpoint, data=data, headers=headers)
    return resp
    print(resp.status_code)
    print(resp.text)
    ...

# Func to send message to a room
# Takes message and the roomId
# Message param is a list with two elements the title of the message and the message body
# RoomId is used to specifiy a specifc room


def send_room_msg(msg, roomId):
    data = {
        'roomId': roomId,
        'text': msg,
        'markdown': f'<blockquote class=danger> <strong>\n{msg[0]}</strong> {msg[1]} '
    }

    resp = requests.post(msg_endpoint, data=data, headers=headers)
    return resp
    print(resp.status_code)
    print(resp.text)
    ...

# Func to send a message with an attachment to a specific roomId
# Uses the MultipartEncoder from request_toolbelt to encode the data along with attachment to be sent to webex
# All according to webex docs
# Takes three params message, file name, and the roomId
# the message param is just a sting containing title
# file name is the name of the attachment to send
# the filename is then used in the data obj files property to open that file
# Headers obj is updated with a Content-type property of the data being encoded and sent


def send_attachment(msg, filename, roomId):
    data = encode({
        'roomId': roomId,
        'text': msg,
        'markdown': f'<blockquote class=danger> <strong>\n{msg}</strong> ',
        'files': (filename, open(filename, 'rb'))
    })

    headers.update({'Content-Type': data.content_type})
    resp = requests.post(msg_endpoint, headers=headers, data=data)
    return resp
    print(resp.status_code)
    print(resp.text)
    ...


# Partial functions built off the ones above to do a specific task as Bottrix
send_loan_room_msg = partial(send_room_msg, roomId=loaned_devices_room_token)
send_loan_attachment = partial(
    send_attachment, roomId=loaned_devices_room_token)

# send_attachment('hello', 'bottrix.py', 'fasifbsa')
# send_room_msg('hello', 'fasifbsa')
# dev = {
#     'device': 'AIR-CT3504-K9',
#     'quantity': 1,
#     'count_down': 'Due in 12 days',
#     'return_date': 'Mar 29, 2022',
#     'case': 'https://lions-ng.cisco.com/case/468993'
# }
