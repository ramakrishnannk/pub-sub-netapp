You should have rabbitmq installed in the system:

This will provide you with:
1.  rabbitmq-server that will help you to create a message broker (in python using 
	pika library functions).
2.  rabbitmqctl that will help you to see the status of the message queues, list 
	channels, virtual hosts, users. Using rabbitmqctl, we can also add and delete 
	users, virtual hosts

For debian based systems like Rasbian for raspberry pi, we can get it from the 
advanced packaging tool (apt). All you have to do is open up the terminal and type:

$ sudo apt-get install rabbitmq-server

For installing pip in the system, we run the following command:

$ sudo apt-get install python-pip

Installing rabbitmq library pika which is python's rabbitmq implementation

$ sudo pip install pika

######################### For running pistatsview.py ################################

The pistatsview.py is a network application which is based on the Advanced Message 
Queuing Protocol (AMQP), which is an application layer protocol for message oriented
middleware [1]. pistatsview.py is an AMQP based subscriber which subscribes to
raspberry pi's utilization information like min, max and current CPU utilization and
network throughput. It has the capability to filter out only those Raspberry pi 
by parsing a set of routing keys whose information is what we require.

*************************								 *************************
************************* 	   ********************	     *************************
**** AMQP Publisher  **** ---> ** Message Broker ** ---> **** AMQP Subscriber ****
*************************	   ********************	     *************************
*************************								 *************************

Assuming the login user as netapp and password as abc123. Assuming virtual host's 
name is test and that the permissions to configure, read and write the virtual 
host's resources for the user netapp is "*.".

Since I have used tabulate library to display the CPU and Network stats, also execute 
the following command

$ sudo pip install tabulate

After installing tabulate python module, go ahead and run the pistatsview.py as 
follows:

$ ./pistatsview.py -b message_broker [-p virtual_host] [-c login:password] -k routing_key

Here, message_broker follows -b option and it is mandatory. It is the server 
hostname or IP address where rabbitmq server is running.

virtual_host follows -p option and is optional as it has a default value of '/'. 
If entered should be valid, should have set permissions using rabbitmqctl 
application.

login:password follows -c option and it is optional as it takes a default value of 
guest:guest. If entered should be valid, should have set permissions to the 
corresponding virtual host using the rabbitmqctl application.

routing_key follows -k option and it is a mandatory one. It is used when we bind the
exchange with the queue so that we filter out those routing keys which we enter here.

NOTE: We can enter multiple routing keys and the application is capable of 
subscribing to utilzation information of more than one raspberry pi.

######################### For running pistatsd.py #####################################
