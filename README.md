# Face Encoding API

## Solution architecture
### API:
Built on top of **FastAPI** which allows to handle a large number of requests per second with low latency.
- `/uploadfile/`: endpoint to upload and validate image. 
Assigns uuid, renames and saves image in file storage for further processing. 
Responds with uuid for later face encoding retrieval.
- `/face_encoding/<uuid>/`: endpoint to retrieve face encoding and status of operation.
- `/stats/`: endpoint to get total number of processed images and number of images processed grouped by status. 

### Image processing background task
Face encoding run asynchronous outside API request by separate worker process. 
This allows to distribute workload across servers to reduce the time to completion and the load on the API server.
- Celery + RabbitMQ
- Flower for realtime task progress and history

### Persistent storage
Result of every processed image stored in database.
- PostgreSQL with table model:
````text
id: uuid Primary key
status: varchar ('created', 'completed', 'failed')
face_encoding: float[]
created_at: timestamp
````

### Face encoding calculating
- [face recognition library](https://github.com/ageitgey/face_recognition)

### Deployment
- Dockerized

### Tests
- Pytest

### Improvements
- Cache face encoding result in Redis
- Add database migration tool alembic
- File storage outside API server 
- Monitoring with Sentry, Datadog