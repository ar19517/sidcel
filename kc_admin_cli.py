import requests
import json
import base64

# Run docker Keycloak container with the command
# docker run -p 8080:8080 -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin -d quay.io/keycloak/keycloak:10.0.2
# install:  python -m pip install requests

# auth_server_url = 'http://192.168.99.100:8080/auth/'
auth_server_url = 'http://localhost:8080/auth/'


""" 1.  The response of the authentication request includes an access, id and refresh token.
        All three of them are Json Web Tokens (JWT). We are interested in the id token.
        Please show the body of the token in a human readable way. """

token_url = auth_server_url + 'realms/master/protocol/openid-connect/token'
payload = {
    'client_id': 'admin-cli',
    'grant_type': 'password',
    'username': 'admin',
    'password': 'admin',
    'scope': 'openid'
}
token_response = requests.post(token_url, payload)
token_response_json = json.loads(token_response.content)

# id token payload decoded and formatted output
id_token = token_response_json['id_token']
id_token_payload = str(id_token).split('.')[1]
id_token_payload_decoded_string = base64.b64decode(id_token_payload)
id_token_payload_dictionary = json.loads(id_token_payload_decoded_string)
print("Keycloak ID Token Payload = "
      + json.dumps(id_token_payload_dictionary, sort_keys=True, indent=4))


# access token and headers for further requests
access_token = token_response_json['access_token']
headers = {
   'content-type': 'application/json',
   'Authorization': 'Bearer ' + access_token
}


""" 2.   Create three realms and within each realm a client with any configuration. """

for i in range(0, 3):
    realm_url = auth_server_url + 'admin/realms'
    payload = {
        "enabled": "true",
        "id": "realm" + str(i),
        "realm": "realm" + str(i)
    }
    requests.post(realm_url, headers=headers, json=payload)

    client_url = realm_url + '/realm' + str(i) + '/clients'
    payload = {
        "enabled": "true",
        "clientId": "realm" + str(i) + "_client",
        "protocol": "openid-connect",
        "publicClient": "false",
        "redirectUris": ["https://www.ruv.de/"]
    }
    requests.post(client_url, headers=headers, json=payload)


# get (id of) realm2_client for the following 2 tasks
client_response = requests.get(client_url + "?clientId=realm2_client", headers=headers)
client_response_json = (json.loads(client_response.content))[0]
realm2_client_id = client_response_json['id']


""" 3.  Add another redirect URI to one of the clients.
        Note that the client, that is updated here, is deleted in the next step (task 4) and 
        added again in the following (task 5). Thus, you may want to comment the code out. """

client_response_json['redirectUris'].append("https://www.google.de/")
requests.put(client_url + "/" + realm2_client_id, headers=headers, json=client_response_json)


""" 4.  Delete one of the clients. """

requests.delete(client_url + "/" + realm2_client_id, headers=headers)


""" 5.  Detect that the client is missing and add it again. """

for i in range(0, 3):
    client_url = realm_url + '/realm' + str(i) + '/clients'
    client_response = requests.get(client_url + '?clientId=realm' + str(i) + '_client', headers=headers)
    client_response_json = json.loads(client_response.content)
    if not client_response_json:
        payload["clientId"] = "realm" + str(i) + "_client"
        if i == 2:
            payload['redirectUris'].append("https://www.google.de/")
        requests.post(client_url, headers=headers, json=payload)
