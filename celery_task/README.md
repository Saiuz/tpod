# How to Use it

Celery is a distributed task management framework
In short, it has two components: 
* the task producer, the caller of the task, under our context, the flask app
* the task consumer(the executor service, which is listening the task)

At the producer side, I will call it in the flask app when user is creating classifiers of running detection tasks

At the listener side, we should start a server to listen to the task