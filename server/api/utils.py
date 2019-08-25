import logging
import uuid
import base64


def raise_json_error(exception_class, message):
    raise exception_class(
        body=f'{{"message": "{message}"}}', content_type="application/json"
    )
