# How to Use it

Celery is a distributed task management framework
In short, it has two components: 
* the task producer, the caller of the task, under our context, the flask app
* the task consumer(the executor service, which is listening the task)

At the producer side, I will call it in the flask app when user is creating classifiers of running detection tasks

At the listener side, we should start a server to listen to the task


### How to run the Task consumer
* Under the director 'celery_task'
* sudo celery -A Tasks worker --loglevel=info
* sudo is necessary, since we are launching docker


### Launching Training Job
Base: prototype image of that kind of network
Task: run the training task
After: after running the task, we should commit the container as an image, then remove the container


### Launching Test Job
Base: image of a classifier 
Task: run the server, until the user remove it or the time runs up 
After: after it exceed, just remove the container


### How to build the base image
docker build -t [name of the created image]  .

