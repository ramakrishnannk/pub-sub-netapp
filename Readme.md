################## README.TXT FOR PUBLISH/SUBSCRIBE NETWORK APPLICATION FOR RASPBERRY PI######################
Before running either the publish or subscribe programs (pistatsd and pistatsview, respectively), you should have 
the Pika AMQP module installed on your Raspberry Pi. To do this, be sure to have pip installed:

$ sudo apt-get install python-pip

Once pip is installed on your Raspberry Pi, simply run the following command to install pika:

$ sudo pip install pika

If you will also be running your own RabbitMQ server (the server is required to run these applications and
serves as the "middle-man" between the publisher and subscriber) you must install RabbitMQ.
This will provide you with:
1.  rabbitmq-server that will help you to create a message broker (in python using 
	pika library functions).
2.  rabbitmqctl that will help you to see the status of the message queues, list 
	channels, virtual hosts, users. Using rabbitmqctl, we can also add and delete 
	users, virtual hosts

For debian based systems like Rasbian for raspberry pi, we can get it from the 
advanced packaging tool (apt). All you have to do is open up the terminal and type:

$ sudo apt-get install rabbitmq-server

######################### PISTATSVIEW.PY #####################################################################

The pistatsview.py file is a network application based on the Advanced Message 
Queuing Protocol (AMQP). This is an application layer protocol for message oriented
middleware [1]. pistatsview.py is a subscriber which subscribes to any number of
raspberry pi's utilization information like min, max and current CPU utilization and
network throughput. It has the capability to filter through Raspberry Pi data using routing keys.

*************************								 *************************
************************* 	   ********************	     *************************
**** AMQP Publisher  **** ---> ** Message Broker ** ---> **** AMQP Subscriber ****
*************************	   ********************	     *************************
*************************								 *************************

The pistatsview.py file requires the use of the tabulate library to display the CPU and Network stats. To install
tabulate, execute the following command:

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

######################### PISTATSD.PY #######################################################################

The pistatsd.py file is an app written in python which reads cpu and network interface information from your Raspberry Pi, and publishes it via a RabbitMQ Server to a message exchange.

Note: The Pika module must be installed to run this program (see the installation note in the first section).

The pistatsd.py app runs with the following commmand in the terminal:

$ python pistatsd.py -b message_broker [-p virtual_host] [-c login:password] -k routing_key

There are four command line parameters that can be entered - message_broker (required), virtual host (optional), Login/Password (optional), and routing key (required).

The -b argument for message broker must be a valid host name/IP address designating a server running RabbitMQ. If no message broker is entered, the program will not run.

The -p argument for virtual_host will default to '/' if nothing is entered.

The -c argument for Login/Password must be entered in the format login:password, and the arguments must match a user/password combination listed with permissions in the RabbitMQ server. If no argument is entered, it will default to "guest:guest"

The -k argument for routing key can be anything, and whatever you enter will identify the data as coming from the Raspberry Pi device running this app. If no routing key is entered, the program will not run.

######################## LIST OF NON-STANDARD PYTHON MODULES REQUIRED #######################################
The following is a list of non-standard python modules required to run the included applications. They are mentioned
previously in this readme, but are provided here as a concise summary:

Non-Standard Python Modules:
-Pika
-Tabulate
-RabbitMQ-Server (if running your own server as the message broker)

