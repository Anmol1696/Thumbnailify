import pytest
import time


@pytest.fixture
def get_status(request, make_requests):
    max_retry = 100  # 100s secs wait loop
    def factory():
        for i in range(max_retry):
            resp = make_requests("status", "get", media_id=request.node.media_id)
            if resp.status_code == 102:
                time.sleep(1)
            else:
                break
        return resp
    return factory


@pytest.fixture
def get_thumbnail(request, make_requests):
    def factory():
        return make_requests("thumbnail", "get", media_id=request.node.media_id)
    return factory


@pytest.fixture(autouse=True)
def cleanup(request, make_requests):
    def factory():
        if getattr(request.node, "media_id", None):
            media_id = request.node.media_id
            resp = make_requests("status", "delete", media_id=media_id)
            assert resp.status_code in [204, 404]
    request.addfinalizer(factory)


@pytest.mark.parametrize("filename", ["image1.jpg", "image1.jpeg", "image1.png", "sample.gif"])
def test_correct_images(request, make_requests, image_encoder, verify_image, get_status,
                        get_thumbnail, filename):
    ext = filename.split('.')[-1]
    data = image_encoder(filename)
    headers = {"Content-Type": f"image/{ext}"}
    resp = make_requests("image", "post", data, **headers)
    print("Post image resp: ", resp.text)
    assert resp.status_code == 202
    # Get image status
    request.node.media_id = resp.json()["media_id"]
    media_status_resp = get_status()
    print("Status image status resp:", media_status_resp.text)
    assert media_status_resp.status_code == 200
    # Get thumbnail
    resp = get_thumbnail()
    print("Thumbnail: ", resp.text)
    assert resp.status_code == 200
    assert verify_image(resp.text)


def test_invalid_base64_encoding(config_data, make_requests):
    data = b"abc"
    headers = {"Context-Type": f"image/png"}
    resp = make_requests("image", "post", data, **headers)
    print(resp.text)
    assert resp.status_code == 400


def test_invalid_content_type(make_requests):
    data = b"abcd"
    headers = {"Content-Type": f"cool/png"}
    resp = make_requests("image", "post", data, **headers)
    print(resp.text)
    assert resp.status_code == 415


def test_invalid_images(request, make_requests, image_encoder, get_status):
    data = b"abcd"
    headers = {"Content-Type": f"image/png"}
    resp = make_requests("image", "post", data, **headers)
    print("Post image resp: ", resp.text)
    assert resp.status_code == 202
    # Get image status
    request.node.media_id = resp.json()["media_id"]
    media_status_resp = get_status()
    print("Status image status resp:", media_status_resp.text)
    assert media_status_resp.status_code == 400
