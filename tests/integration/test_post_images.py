import pytest


@pytest.mark.parametrize("filename", ["image1.jpg", "image1.jpeg", "image1.png"])
def test_correct_post(config_data, make_requests, image_encoder, verify_image, filename):
    ext = filename.split('.')[-1]
    data = image_encoder(filename)
    headers = {
        "Content-Type": f"image/{ext}"
    }
    resp = make_requests("image", "post", data, **headers)
    print(resp.text)
    assert resp.status_code == 202
