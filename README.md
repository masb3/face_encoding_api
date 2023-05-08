# Face Encoding API

## Solution architecture
### API:
Built on top of **FastAPI** which allows to handle a large number of requests per second with low latency.
- `/uploadfile/`: endpoint to upload and validate image. 
Assigns uuid, renames and saves image in file storage for further processing. 
Responds with uuid for later face encoding retrieval.
- `/face_encoding/<uuid>/`: endpoint to retrieve face encoding and status of operation.
- `/stats/`: endpoint to get total number of processed images and number of images processed grouped by status. 
- `/bonus/`: calculates the average face encodings for all previously calculated images.   
Fetch multiple rows without loading them all into memory at once and calculate average in async for loop.  

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
- Multiple files upload
- File storage outside API server 
- Monitoring with Sentry, Datadog
- Bonus API accept timeperiod in query parameter to limit number of face encodings to calculate average.  
Set default to some meaningful period



## HOWTO
Create `.env` file in the project root folder
```commandline
POSTGRES_USER="dummy"
POSTGRES_PASSWORD="dummy"
POSTGRES_DB="dummy"
DATABASE_URL="postgresql://dummy:dummy@db:5432/dummy"

CELERY_BROKER_URL="amqp://dummy:dummy@rabbitmq:5672//"
CELERY_RESULT_BACKEND="redis://redis:6379/0"

RABBITMQ_DEFAULT_USER="dummy"
RABBITMQ_DEFAULT_PASS="dummy"
```
To run program execute command in project root:  
```
docker compose up --build -d
```  
To run tests execute command in project root:  
```
docker compose exec api pytest
```  
Tested with Docker v23.0.5  

Note: hardcoded host ports
- `5001` - FastAPI service
- `55055` - Flower monitoring  

These can be changed in [docker-compose.yml](https://github.com/masb3/face_encoding_api/blob/main/docker-compose.yml)

### API requests
- `/uploadfile/`: 
```
curl -F "file=@/path/to/file/file.jpg" http://localhost:5001/uploadfile/
```
- `/face_encoding/<uuid>/`: 
```
curl http://localhost:5001/face_encoding/<uuid>
```
- `/stats/`: 
```
curl http://localhost:5001/stats/
```  
- `/bonus/`: 
```
curl http://localhost:5001/bonus/
```  
