import hmac
import hashlib
import json
import base64


class BadSignature(Exception):
    '''The signature is'''
    pass


class HMACSigner:

    def __init__(self, key: str, separator: str = ':', encoding: str = 'utf8'):
        self.key = key.encode()
        self.separator = separator
        self.encoding = encoding

    def signature(self, message: str) -> bytes:
        '''Sign the message using HMAC and return base64 encoded signature'''
        return hmac.new(self.key, message.encode(self.encoding), hashlib.sha1).digest()

    def base64_signature(self, message: str) -> str:
        return base64.b64encode(self.signature(message)).decode(self.encoding)

    def sign(self, message: str) -> str:
        '''Return message:signature where the signature is HMAC signature'''
        signature = self.base64_signature(message)
        return f'{message}{self.separator}{signature}'

    def verify(self, signed_message: str) -> str:
        '''Return the message if given signed message is valid'''
        if self.separator not in signed_message:
            raise BadSignature(f'No `{self.separator}` found in message')
        message, message_signature = signed_message.rsplit(self.separator, 1)
        signature = self.signature(message)
        message_signature = base64.b64decode(message_signature)
        if hmac.compare_digest(signature, message_signature):
            return message
        raise BadSignature('Signature is not valid')


class TimeStampedHMACSigner(HMACSigner):
    pass


def hmac_json_dumps(obj: dict, key: str) -> str:
    '''Dump the dictionary object as json and sign it using hmac.'''
    serialized_data = json.dumps(obj, separators=(',', ':')).encode('utf8')
    serialized_data = base64.b64encode(serialized_data).decode('utf8')
    singer = HMACSigner(key=key)
    return singer.sign(serialized_data)
