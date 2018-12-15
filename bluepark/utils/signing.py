import hmac
import hashlib
import json
import base64


def hmac_json_dumps(obj: dict, key: bytes) -> str:
    '''Dump the dictionary object as json and sign it using hmac.'''
    serialized_data = json.dumps(obj, separators=(',', ':')).encode('utf8')
    signed = hmac.new(key, serialized_data, hashlib.sha1)
    return base64.b64encode(signed.digest()).decode()
