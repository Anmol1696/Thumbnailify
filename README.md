# Thumbnailify
Service for creating thumbnails from photos

Using Media instead of Image, so as to extend to video and gif in the future

## Tech Stalk
- Web Server
  - Python
  - aiohttp
  - aioamqp
  - aiocassandra
- Datastore
  - cassandra
- Worker
  - Python
- Queue
  - Rabit MQ

### Testing
- Integration Tests
  - Pytest
- Stress Tests
  - Locust

### Deployment
- Docker-compose
- k8s deployments (deployed on MiniKube with scaling)

## Web Server
Using Aiohttp, use header with `Content-type:image/*` to specify the header
Use Aiofiles to save the images appropreatly
MD5 hash of base64 encoded image is returned as `media_id`

## Database
The tables in database will look like,
- `thumb_id` MD5 hash of base64 encoded thumbnail
- `message` stores any error message, in case of completion, `message="Completed"`
- `status_code` 200 incase of complition, 400 incase the input image was corroupted, 500 incase of thumbnail creation errors
- `media_type` will define the image and thumbnail filenames as well in the file sytem

`media_id, media_type, thumb_id, message, status_code` (add `thumb_data` here instead of database)

Status code in the database can used for cleaning up corroupted images. Incase the image was
corroupted, the new correct image will not have the same base64 hash anyways
If `media_id` is same, that means there was an error

Using MD5 hash as it has the same length as a UUID. SHA will be too big of an ID.

For now `media_type` will be `image/*`

## Workers
Worker will be consuming the RabitMQ worker tasks


## File Storage
File storage will be common Volumes, raw images and thumbnails will be stroed in seperate folders
`raw` and `thumb` respectively. The filenames will be `{image_id/thumb_id}.{media_type}`

## Rabit MQ
`https://www.rabbitmq.com/confirms.html`
