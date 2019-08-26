# Thumbnailify
Service for creating thumbnails from photos

Using Media instead of Image, so as to extend to video and gif in the future

#### NOTE: Sorry in advance for alot of spelling mistakes, will try to catch them all

## Tech Stack
- Web Server
  - Python
  - aiohttp
  - aioamqp
  - aiofiles
  - aioredis
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
| `/images/<id>` | `DELETE` | Delete file, thumbail and entry in database | Done |
| `/images/<id>/thumbnail` | `GET` | Get thumbail as base64 encoded data with type in header | Done |

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


## General Notes on Design
### Microservice Design
- Microservices arch best practices recommends there should be no database sharing, each service should maintain there oown data/state etc.
- Might not be a good idea sharing both db and filesystems between worker and webserver, if we were to consider workers as a service (WAAS).
- Not super sure about how filesystems are handled in micro services. One way could be to create a FileSystem as a service, that stores and gets files. But in cases for large files this might jam up the network too.

### Event Driven Design
- Event Driven design with Kafka or Pub/Sub can allow us to merge both the DB and the queue into one.
- Use kafka as the single source of truth. The state of the media can also be managed easily by each process being pushed back into Pub/Sub. Finding the state of the operation will be more transparent
- Filesystem might be best kept seperate


