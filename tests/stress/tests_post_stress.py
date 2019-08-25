import random
import json
import time
from pathlib import Path

from locust import HttpLocust, TaskSequence, seq_task, task
from locust.events import request_failure

from tests.utils import load_config, file_encoder

config = load_config()


class UserBehavior(TaskSequence):
    def on_start(self):
        self.image_data = {}
        for image in config["data"]["images"].split(','):
            self.image_data[image] = file_encoder(Path(config["data"]["dir"]) / image)

    @seq_task(1)
    def send_image(self):
        image = random.choice(list(self.image_data.keys()))
        self.ext = image.split('.')[-1]
        response = self.client.post(
            "/images",
            name="Send Image",
            data=self.image_data[image],
            headers={"Content-Type": f"image/{self.ext}"}
        )
        self.image_id = response.json().get("id")

    @seq_task(2)
    @task(10)
    def check_status(self):
        self.client.get(
            f"/images/{self.image_id}",
            name="Get Image Status"
        )


# Added this for receiving more detailed output of the failed requests.
def on_failure(request_type, name, response_time, exception, **kwargs):
    print(exception.request.url)
    print(exception.response.status_code)
    print(exception.response.content)


request_failure += on_failure


class ThumbnailifyUser(HttpLocust):
    host = config["DEFAULT"]["base-url"]
    task_set = UserBehavior
