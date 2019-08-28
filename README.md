# Thumbnailify
Service for creating thumbnails from photos

#### NOTE: Sorry in advance for alot of spelling mistakes, will try to catch them all

## Tech Stack
- Web Server
  - Python
  - aiohttp
  - aioamqp - async amqp python implementation
  - aiofiles - async files module
  - aioredis - async redis library
- Datastore
  - redis
- Worker
  - Python
- Queue
  - Rabit MQ
- Filesystem

### Testing
- Integration Tests
  - Pytest
- Stress Tests
  - Locust

### Deployment
- Docker-compose
- k8s deployments (Future works)

Using Media instead of Image, so as to extend to videos in the future

## Web Server
### Tech Stack and design
Webserver is built using aiohttp and asyncio libraries. Aiohttp is completly async framework and
performs well in case of i/o bound operations. One advantage of Aiohttp over Flask is it need not
be run with Gunicorn to handle multiple threads. Growing async libraies in python gives this a good
fit.
Many benchmarks online showing clear advantages of aiohttp over flask. Also the framework is highly
flexible and easy to use, once you get a hang of async in python. Async in python is showing alot
of promieses especially after `python3.7`
Using `aiofiles` as async lib for saving and reading files, wrapper `server/db/filesystem`
Using `aioamqp` for queue interactions, wrapper `server/db/rabbitmq`
Using `aioredis` for db interactions, wrapper `server/db/redis`

All db components are dynamically loaded, hence the plugability concept. We can change any of the
underlying tech to another just by writing the wrappers and having the overhead functions
DB engines are loaded to the `app` context on the start of the application as per the config
`config/config.yaml`

### Endpoints
| API Endpoint | Method | Description | Status |
|--------------|--------|-------------|--------|
| `/images` | `GET` | Return all itmes and ids from the database | Future Works |
| `/images` | `POST` | Send Base64 encoded media with media type in headers in `Content-Type` | Done |
| `/images/<id>` | `GET` | Get status of the image and where the image is currently in the workflow | Done |
| `/images/<id>` | `DELETE` | Delete file, thumbail and entry in database, no need for request body | Done |
| `/images/<id>/thumbnail` | `GET` | Get thumbail as base64 encoded data with type in header | Done |

### Request Body
```
POST /images/<id>/thumbnail

Headers: {"Content-Type": "<content ext and type>"} // image/png. image/gif

BASE64 encoded image in Body
```

### Response Bodies
```
GET /images/<id>
{
    "media_id": "<media_id uuid>",
    "media_type": "<content type>", // sample, image/png. image/gif
    "service": "<last service that updated this log>", // worker, webserver
    "message": "<current message>",
    "state": "<Current state of media>" // Error, Processing, Completed
}
```
```
GET /images/<id>/thumbnail

Headers: {"Content-Type": "<content ext and type>"} // image/png. image/gif

BASE64 encoded image in Body
```

### WorkFlow
- User sends media data to the `/images` endpoint as base64 encoded text as POST with header `Content-Type=image/<png or jpg or jpeg>`
- Media is decoded, stored to filesystem, `media_id` sent to queue, response is sent to the user (for this process the user is kept waiting, since this step wont take long and any error is conveyed to the user)
- In Response `media_id` (randomly generated uuid) with other metadata is returned in case of sucess with code 202 (`HTTPAccepted`)

### Note
- Webserver does not check the incoming data, hence even if the media is corroupted but the request body has correct base64 encoding, the data will be stored in the file system and an id will be generated
- For each `POST` unique uuid is generated for now, later can chaange to hash of the body to avoid same data being processed again and again
  - Droped hashing of body for now, since the body needed to be read twice with added cost of computing a simple hash which is a sync process. For large huge size data, this will become a problem
  - Stress testing becomes easy to calculate the throughput of the application with limited test data
- Webserver is written in plugable components form which will make it very easy to
  - add various media types, with practially no effort (have to check the worker, server can take various contents)
  - change the components of database, queue as well as filesystems since all have a client wrapper and related functions enclosed with that wrapper
- Delete endpoint is for mostly testing, so as to stress tests without blowing up the harddisks as well as redis (which is more less likely)


## Database
### TechStack
Redis is used as key value store for maintaining the state of the system. In future I would higly recommed cassandra, since it is highly available with no single point of failure. It scales very well.

### DataStructure
Using Hash map of redis to store media state data as dict value and `media_id` as key
Since using small number of fields in this manner is considerd fast enough (a/c offical redis docs
small is 100 fields),
Current structure is, each key (`media_id`) has the following fields with possible entry values
- `media_type`: `image/png`, `image/jpg`, `image/jpeg`... In not so future (`video/mp4`, `image/gif`)
- `service`: Service where the media was last processed, `webserver` or `worker`
- `state`: One of `Processing`, `Completed`, `Error` (Any error from encountered by worker)
- `message`: Msg from server or worker for now
- `code`: Status code to be returned in case of GET `/images/{media_id}`

### Note
- k8s has the concepts of desired state and observed state, this can be a useful insight to include in the datastore. Not just the current state and status, but a list of all previous actions as well as current state. Wiil require much wider database
- Current data strucutre is minimum viable data required, can think of more valuable data in the future including paths of raw and thumnails as well. (currectly both server and worker have a config entry telling them where are the raw files and where are the thumbnail)


## File Storage
Using shared volume for storing incoming raw media as well as thumbnail image that are created
Use 2 folders, for storing raw/input media and other for thumbnail
Filesystems are good enough, but we can use `DBFS` too if nessasary
2 Folders also ensures, that worker and webserver are reading from one and wrting to other, to avoid
corrouption of data in the long run

## Rabit MQ
Using simple work queues. This is good incase of multiple workers. Queue message is the `media_id`
with `media_type` in the header of the message. The `media_type` is sent by the server to reduce a
call to the datastore from the worker (since worker just needs the `media_id` and `media_type` to find the file in the filesystem)


## Workers
### TechStack and design
Worker is writen in pure python and is blocking and sync. This is by design since the main job of
the worker is to chunck media into thumnails which is a slow process. Using python `wand` lib that
uses ImageMagick. Using `pika` for rabbit-mq lib and `redis` lib for redis

The worker is written more crudely and less plugable since the whole worker itself is very light
and limited. Idea was to have multiple workers and well as different kinds of workers in the future.

The capability of worker to crunch the media itself is plugable and extendable easily. in `ThumbHandler` in `worker/thumbnail.py`

### WorkFlow
- worker waits on the queue, to get a message
- reciving `media_id`, trys to process and create a thumbnail of size `100x100`
- Update db entry by the state, message, code, of either sucsess or any error
- Raw media file is deleted after it has been processed
- Ack sent to the queue, (in case of sucess or failure, since the media was processed and db updated)

### Notes
- Worker can handle some exceptions, but there is not `try/except` block for the main function, hence the workers need to be deployed with some sort of restart and deployment policies in docker-compose or k8s itself
- Raw media file is deleted for testing purposes and making sure the disk space doesn't increase (better to comeup with some retension policies)


## Running System
- Using Makefile, `make`, this basically runs `docker-compose up`, these start following
  - 1 Container of web-server
  - 1 Redis Container
  - 1 Rabbit MQ Container
  - 2 Worker Container (Replicas can be increased for better performance)
- Docker-compose has a flag for linking dependencies of containers, but I was not able make starting of server and worker before redis actually starts, hence both worker and server keeps on restarting untill it works, can be solved by health checks in k8s deployment or statefull sets
- Better to creating services and deployments in K8s


## Testing
### Integration Tests
- Integration Tests in `pytest`
- Currently all tests are end to end tests. Idealy each endpoint should have its own set of tests so as to find out the exact point of failure, while we are developing and debuging code
- For running the integration tests, we run these tests against a working full service, with server, worker, redis, rabbitmq.
- Integration tests come with default test data, in the `Thumbnailify/tests/data`

#### Running Test
- Need a running system, if system running at some address, can modify `Thumbnailify/tests/conf.ini``base-url` entry
- By using Makefile `make test-integration`
- Direct run `pytest -vv -x --tb=auto`

#### Results
```
$ make test-integration
pytest -vv -x --tb=auto
========================================= test session starts ==========================================
platform linux -- Python 3.7.3, pytest-5.0.0, py-1.8.0, pluggy-0.12.0 -- /usr/bin/python3.7
cachedir: .pytest_cache
rootdir: /home/anmol/Documents/personal/git/Thumbnailify
plugins: slack-2.0.0
collected 7 items

tests/integration/test_post_images.py::test_correct_images[image1.jpg] PASSED                    [ 14%]
tests/integration/test_post_images.py::test_correct_images[image1.jpeg] PASSED                   [ 28%]
tests/integration/test_post_images.py::test_correct_images[image1.png] PASSED                    [ 42%]
tests/integration/test_post_images.py::test_correct_images[sample.gif] PASSED                    [ 57%]
tests/integration/test_post_images.py::test_invalid_base64_encoding PASSED                       [ 71%]
tests/integration/test_post_images.py::test_invalid_content_type PASSED                          [ 85%]
tests/integration/test_post_images.py::test_invalid_images PASSED                                [100%]

======================================= 7 passed in 9.79 seconds =======================================
```
#### Conclusions and Improvements
- Tests do not cover the all overall cases, but some cases of data corrouption that might happen from data transfer or packet dropping, that are also considered can not be modeled unless we seperate out the tests for worker and server (Future work, worker tests, server tests and existing e2e tests)
- Running Integration tests with failure tests, that is, finding the behavior of the system incase some or more services are down. Example, what happens when filesystem is down, redis is down, queue is down

### Stress Tests
- Running stress tests with Locust, a simple python load generator
- Locust doesn't create constant loads, but more like, mimics user behaviour, alternative and future work would be tests with Jmeter
- Reasons of choosing locust
  - Strong support for python for creating load and user behaviour
  - Good UI with real time charts and simple web UI
  - Can be distributed in the future
  - Good for quick stress tests
- Tests are for sending image and checking the status of the image, thumbnail endpoint is not load tested for now, can be added very easiliy
- User behavior that is stress tested is as follows
  - User makes a `Post` request to `/images` endpoint, and get `media_id`
  - Check the status of media by `Get` at `/images/{media_id}`, this step happens 10 times
- Locust has concept of `Number of unique users` and `Hatch rate`. In short this does the following
  - `Hatch rate` number of users will be spawned for every second until it reached `Number of unique users`
  - Each users does the above mentioned, `Post`, `Get` (10 times)`
  - Loucst gives a number `RPS` which is the thoughput that our system can handle
- Docker Volume needs to be dropped after performing stress tests, since the images will just start pilling up (Need a better solution)

##### NOTE
```
Overall throughput tends to decrease as you increase the response time for an average transaction.
The reason is that after sending the 1st request, locust needs to wait until the request to be
completed/processed to send the 2nd request. So that it’s tricky to use Locust if you want to
have a fixed throughput.

Good Read (https://medium.com/@linh22jan/load-test-with-locust-37c4f85ee2fb)
```

### Running Tests
- Test run against running system, if running system at some other IP, update `Thumbnailify/tests/conf.ini`, `base-url`
- Using make, `make test-integration` starts the locust at 8089 port, there you can specify number of unique users and hatch rate.
  - Running stress without UI as `locust -f --no-web -c <users> -r <hatch-rate> --run-time 1h30m`

### Results
Running 2 workers, 1 server, 1 redis, 1 rabbit mq

For less number of simultaneous users and hatch rate

![Stress low users](https://github.com/Anmol1696/Thumbnailify/blob/master/bin/thumb_start.gif)

For higher number of simultaneous users and hatch rate

![Stress high users](https://github.com/Anmol1696/Thumbnailify/blob/master/bin/thumb_end.gif)

```
 Name                                                          # reqs      # fails     Avg     Min     Max  |  Median   req/s
--------------------------------------------------------------------------------------------------------------------------------------------
 GET Get Image Status                                          141722     0(0.00%)     277       3    1333  |     230  292.30
 POST Send Image                                                14500     0(0.00%)     364       4    1504  |     320   39.70
--------------------------------------------------------------------------------------------------------------------------------------------
 Total                                                         156222     0(0.00%)                                     332.00

Percentage of the requests completed within given times
 Name                                                           # reqs    50%    66%    75%    80%    90%    95%    98%    99%   100%
--------------------------------------------------------------------------------------------------------------------------------------------
 GET Get Image Status                                           141722    230    330    400    450    590    700    830    910   1300
 POST Send Image                                                 14500    320    440    530    590    730    850   1000   1100   1500
--------------------------------------------------------------------------------------------------------------------------------------------
 Total                                                          156222    240    340    410    460    600    720    850    940   1500
```

### Conclusion
- Aiohttp servers need to be scaled out, not up, since it is bound by I/O calls
- Exact bottle necks need to be figured out by monitoring and logging checks
- Running on local machine, running on bigger cluster and dedicated resources, better results


## Code Improvements and Production Ready
- Python exceptions are handled loosely now, using `except Exception` is not a good practice, since the excetions should be more precise
- Logging can be improved, server logs not following the log format, needs some debugging
- Tests are not automated, can be automated based on the CI/CD pipelines as well as creating test services and deployments, automatic generation of reports
- For production, using k8s with auto scaling, monitoring to figure out the bottle necks of the systems, alerts on logs and services by either ELK or using coustom GPC (no idea of inbuilt in tools that GCP provides, yet !!)


## General Notes on Design Improvements
### Microservice Design
- Microservices arch best practices recommends there should be no database sharing, each service should maintain there oown data/state etc.
- Might not be a good idea sharing both db and filesystems between worker and webserver, if we were to consider workers as a service (WAAS).
- Not super sure about how filesystems are handled in micro services. One way could be to create a FileSystem as a service, that stores and gets files. But in cases for large files this might jam up the network too.

### Event Driven Design
- Event Driven design with Kafka or Pub/Sub can allow us to merge both the DB and the queue into one
- Use kafka as the single source of truth. The state of the media can also be managed easily by each process being pushed back into Pub/Sub. Finding the state of the operation will be more transparent
- Filesystem might be best kept seperate, not sure how filesystems are handled in microservice arch.

### Performance and More research
- Scaling out will increase the through-put, there are 3 main issues that could be the bottle necks
  - File I/O, reading and writing from the server is done using aiofiles
  - Scaling out queue and db also will be required when scalling the server, else they will become the bottlenecks
- Exact bottle necks can be identified only after logging and monitoring (Not enough exp with scalling)
- Base64 encoding increases the data by 33%, since images are any way bigger then std http request body, better to use compression with content-type `gzip` or something similar (need more research in that direction)
- Upper limit of http body is hit for with 1MB size, hence only small images and Gif work, solution could be to accept it in a stream, but there must be a better way
