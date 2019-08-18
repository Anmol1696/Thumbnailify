import logging

logger = logging.getLogger("aiohttp.application")

def raise_json_error(exception_class, message):
    raise exception_class(
        body=f'{{"message": "{message}"}}', content_type="application/json"
    )
