You should have rabbitmq installed in the system:

This will provide you with:
1.  rabbitmq-server that will help you to create a message broker (in python using pika library functions).
2.  rabbitmqctl that will help you to see the status of the message queues, list channels, virtual hosts, users.
    Using rabbitmqctl, we can also add and delete users, virtual hosts

For debian based systems like Rasbian for raspberry pi, we can get it from the advanced packaging tool (apt).
All you have to do is open up the terminal and type:

$ sudo apt-get install rabbitmq-server


