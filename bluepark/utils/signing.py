import base64
import hashlib
import hmac
import json
import time


class BadSignature(Exception):
    '''The signature is not valid'''
    pass


class ExpiredSignature(Exception):
    '''Signature is expired'''
    pass


def b64encode(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data)


def b64decode(data: bytes) -> bytes:
    return base64.urlsafe_b64decode(data)


class HMACSigner:

    def __init__(self, key: str, separator: str = ':', encoding: str = 'utf8'):
        self.key = key.encode()
        self.separator = separator
        self.encoding = encoding

    def signature(self, message: str) -> bytes:
        '''Sign the message using HMAC and return base64 encoded signature'''
        return hmac.new(self.key, message.encode(self.encoding), hashlib.sha1).digest()

    def base64_signature(self, message: str) -> str:
        return b64encode(self.signature(message)).decode(self.encoding)

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
        message_signature = b64decode(message_signature.encode(self.encoding))
        if hmac.compare_digest(signature, message_signature):
            return message
        raise BadSignature('Signature is not valid')


class TimeStampedHMACSigner(HMACSigner):
    '''Use HMAC to sign the message and include timestamp in to the message.'''

    def sign(self, message: str) -> str:
        timestamp = b64encode(str(int(time.time())).encode(self.encoding)).decode(self.encoding)
        return super().sign(f'{message}{self.separator}{timestamp}')

    def verify(self, signed_message: str, max_age: int = None) -> str:
        timestamped_message = super().verify(signed_message)
        if self.separator not in timestamped_message:
            raise BadSignature(f'No `{self.separator}` found in message')
        message, timestamp = timestamped_message.rsplit(self.separator, 1)
        if max_age is None:
            return message
        timestamp = int(b64decode(timestamp).decode(self.encoding))
        if timestamp + max_age < time.time():
            raise ExpiredSignature()
        return message


def hmac_json_dumps(obj: dict, key: str) -> str:
    '''Dump the dictionary object as json and sign it using hmac.'''
    serialized_data = json.dumps(obj, separators=(',', ':')).encode('utf8')
    serialized_data = b64encode(serialized_data).decode('utf8')
    signer = TimeStampedHMACSigner(key=key)
    return signer.sign(serialized_data)


def hmac_json_loads(message: str, key: str, max_age: int = None) -> dict:
    '''Dump the dictionary object as json and sign it using hmac.'''
    signer = TimeStampedHMACSigner(key=key)
    decoded_message = b64decode(signer.verify(message, max_age).encode('utf8')).decode('utf8')
    return json.loads(decoded_message)
