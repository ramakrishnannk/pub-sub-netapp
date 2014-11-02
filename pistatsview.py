#!/usr/bin/python

import json
import pika
import pika.channel
import pika.exceptions
import signal
import sys
from tabulate import tabulate

# Create a data structure for holding the maximum and minimum values
stats_history = {"cpu": {"max":0.0, "min": float("inf"), "current": 0.0}, "net": dict()}

class StatsClientChannelHelper:
    """
    This helper class is used to manage a channel and invoke event handlers when signals are intercepted
    """

    def __init__(self, channel):
        """
        Create a new StatsClientChannelEvents object

        :param channel: (pika.channel.Channel) The channel object to manage
        :raises ValueError: if channel does not appear to be valid
        :return: None
        """

        if isinstance(channel, pika.channel.Channel):
            self.__channel = channel

        else:
            raise ValueError("No valid channel to manage was passed in")

    def stop_stats_client(self, signal=None, frame=None):
        """
        Stops the pika event loop for the managed channel

        :param signal: (int) A number if a intercepted signal caused this
                        handler to be run, otherwise None
        :param frame: A Stack Frame object, if an intercepted signal caused this handler to be run
        :return: None
        """
        # TODO: Attempt to gracefully stop pika's event loop
        self.__channel.stop_consuming()

def show_stats_history(stats_history, routing_key):
    """
    Displays stats history invoked by the event handler

    :param stats_history: Data structure that holds the latest minimum and maximum values
    :return None

    NOTE: We use package called tabulate to display the stats, Following url gives the source
    url: https://pypi.python.org/pypi/tabulate
    """
    # Print the routing key whose message gets printed below:
    print "%s :" %(routing_key)

    cpu_table = [["Type", "Current", "High", "Low"], ["CPU", stats_history["cpu"]["current"], stats_history["cpu"]["max"], stats_history["cpu"]["min"]]]

    print tabulate(cpu_table)

    net_table = [["Type", "Interface", "Tx/Rx", "Current", "High", "Low"]]
    for iface in stats_history["net"].keys():
        for iface_mode in ("rx", "tx"):
            net_table.append(["NET", iface, iface_mode, stats_history["net"][iface][iface_mode]["current"], stats_history["net"][iface][iface_mode]["max"], stats_history["net"][iface][iface_mode]["min"]])

    print tabulate(net_table)

def on_new_msg(channel, delivery_info, msg_properties, msg):
    """
    Event handler that processes new messages from the message broker

    :param channel: (pika.Channel) The channel object this message was received from
    :param delivery_info: (pika.spec.Basic.Deliver) Delivery information related to the message just received
    :param msg_properties: (pika.spec.BasicProperties) Additional metadata about the message just received
    :param msg: The message received from the server
    :return None
    """

    # Parse the JSON message into a dict
    try:
        stats = json.loads(msg)

        # Check that the message appears to be well formed
        if "cpu" not in stats:
            print "Warning: ignoring message: missing 'cpu' field"

        elif "net" not in stats:
            print "Warning: ignoring message: missing 'net' field"

        else:
            # Message appears well formed

            # Evaluate CPU field for max/min status
            if stats["cpu"] > stats_history["cpu"]["max"]:
                stats_history["cpu"]["max"] = stats["cpu"]
            if stats["cpu"] < stats_history["cpu"]["min"]:
                stats_history["cpu"]["min"] = stats["cpu"]

            # Store the current CPU value
            stats_history["cpu"]["current"] = stats["cpu"]

            # Evaluate NET field for max/min status
            for iface in stats["net"].keys():
                # Has the current iface been seen before?
                if iface not in stats_history["net"]:
                    # No, create a new entry for the iface
                    stats_history["net"][iface] = {"rx":{"max":0.0, "min":float("inf"), "current":0.0}, "tx": {"max":0.0, "min":float("inf"), "current":0.0}}

                # Check if the iface key is well formed
                if "rx" not in stats["net"][iface]:
                    print "Warning: ignoring interface: " + iface + ": no 'rx' field"
                    continue

                elif "tx" not in stats["net"][iface]:
                    print "Warning: ignoring interface: " + iface + ": no 'tx' field"
                    continue

                else:
                    # Evaluate max and min for each iface mode
                    for iface_mode in ("rx", "tx"):
                        # Store new global max
                        if stats["net"][iface][iface_mode] > stats_history["net"][iface][iface_mode]["max"]:
                            stats_history["net"][iface][iface_mode]["max"] = stats["net"][iface][iface_mode]
                        # Store new global min
                        if stats["net"][iface][iface_mode] < stats_history["net"][iface][iface_mode]["min"]:
                            stats_history["net"][iface][iface_mode]["min"] = stats["net"][iface][iface_mode]

                        # Store the current value
                        stats_history["net"][iface][iface_mode]["current"] = stats["net"][iface][iface_mode]

            # Print the max, min and current stats value to stdout
            show_stats_history(stats_history, delivery_info.routing_key)

    except ValueError, ve:
        # Thrown by json.loads() if it couldn't parse a JSON object
        print "Warning: Discarding Message: received message couldn't be parsed"

# Application Entry Point
# ^^^^^^^^^^^^^^^^^^^^^^^

# Guard try clause to catch any errors that aren't expected
try:
    # The message broker hostname or IP address
    host = "localhost"

    # The virtual host to connect to
    vhost = "/" # Defaults to the root virtual host

    # The credentials to be used
    credentials = None

    # The topics (list of topic) to subscribe to
    topics = []

    # Parse the command line arguments
    if len(sys.argv[1:]) < 1:
        print >> sys.stderr, "Usage: %s -b message_broker [-p virtual_host] [-c login:password] -k routing_key" %(sys.argv[0])
        sys.exit(-1)

    last_argv = sys.argv[len(sys.argv) - 1]
    for i in range(1, (len(sys.argv[1:]) + 1)):
        if sys.argv[i] == '-b':
            if sys.argv[i + 1][0] == '-':
                print >> sys.stderr, "Usage: %s -b message_broker [-p virtual_host] [-c login:password] -k routing_key" %(sys.argv[0])
                sys.exit(-1)
            host = sys.argv[i + 1]
            # print host
        elif sys.argv[i] == '-p':
            if sys.argv[i + 1][0] == '-':
                print >> sys.stderr, "Usage: %s -b message_broker [-p virtual_host] [-c login:password] -k routing_key" %(sys.argv[0])
                sys.exit(-1)
            vhost = sys.argv[i + 1]
            # print vhost
        elif sys.argv[i] == '-c':
            if sys.argv[i + 1][0] == '-' or (not sys.argv[i + 1].count(':') == 1):
                print >> sys.stderr, "Usage: %s -b message_broker [-p virtual_host] [-c login:password] -k routing_key" %(sys.argv[0])
                sys.exit(-1)
            credentials = sys.argv[i + 1]
            # print credentials
        elif sys.argv[i] == '-k':
            if sys.argv[i + 1][0] == '-':
                print >> sys.stderr, "Usage: %s -b message_broker [-p virtual_host] [-c login:password] -k routing_key" %(sys.argv[0])
                sys.exit(-1)
            further_args = sys.argv[(i + 1):]
            j = 0
            while further_args[j][0] != '-':
                topics.append(further_args[j])
                if further_args[j] == last_argv:
                    break
                j += 1
            print topics

    if host is None:
        print >> sys.stderr, "Error: You must specify a message broker to connect to"
        sys.exit(-1)

    if len(topics) == 0:
        print >> sys.stderr, "Error: You must specify at least one topic to subscribe to"
        sys.exit(-1)

    message_broker = None
    channel = None
    try:
        # Connect to the message broker using the given broker address (host)
        # Use the virtual host (vhost) and credential information (credentials), if provided

        if credentials is not None:
            usrname = credentials.split(':').__getitem__(0)
            password = credentials.split(':').__getitem__(1)
            # Check if there is a user with "usrname" else create it
            pika_credentials = pika.PlainCredentials(usrname, password)
        else:
            pika_credentials = None

        pika_parameters = pika.ConnectionParameters(host=host, virtual_host=vhost, credentials=pika_credentials)
        message_broker = pika.BlockingConnection(pika_parameters)

        # Setup the channel and exchange
        channel = message_broker.channel()
        # Exchange declaration, NOTE that this exchange is not a durable one
        channel.exchange_declare(exchange='pi_utilization', type='direct')

        # Setup signal handlers to shutdown this app when SIGINT or SIGTERM
        # is sent to this app
        signal_num = signal.SIGINT
        try:
            # Create a StatsClientChannelEvents object to store a reference
            # to the channel that will need to be shutdown if a signal is caught
            channel_manager = StatsClientChannelHelper(channel)
            signal.signal(signal_num, channel_manager.stop_stats_client)
            signal_num = signal.SIGTERM
            signal.signal(signal_num, channel_manager.stop_stats_client)

        except ValueError, ve:
            print "Warning: Graceful shutdown may not be possible: Unsupported Signal: " + signal_num

        # Create a queue
        # --------------------
        # Creating an exclusive queue NOTE that will only exists
        # as long as the client is connected

        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        # Bind you queue to the message exchange, and register your new message event handler
        for topic in topics:
            channel.queue_bind(exchange='pi_utilization', queue=queue_name, routing_key=topic)

        # Start pika's event loop
        channel.basic_consume(on_new_msg, queue=queue_name, no_ack=True)

        channel.start_consuming()


    except pika.exceptions.ProbableAccessDeniedError, pade:
        print >> sys.stderr, "Error: A Probable Access Denied Error occured: " + str(pade.message)

    except pika.exceptions.ProbableAuthenticationError, aue:
        print >> sys.stderr, "Error: A Probable Authentication error occured: " + str(aue.message)
    
    except pika.exceptions.AMQPConnectionError, acoe:
        print >> sys.stderr, "Error: An AMQP Connection Error occured: " + str(acoe.message)

    except pika.exceptions.AMQPChannelError, ache:
        print >> sys.stderr, "Error: An AMQP Channel Error occured: " + str(ache.message)
    
    except pika.exceptions.ChannelError, ce:
        print >> sys.stderr, "Error: A channel error occured: " + str(ce.message)
    
    except pika.exceptions.AMQPError, ae:
        print >> sys.stderr, "Error: An AMQP Error occured: " + str(ae.message)
    
    except Exception, eee:
        print >> sys.stderr, "Error: An unexpected exception occured: " + str(eee.message)

    finally:
        #TODO: Attempt to gracefully shutdown the connection to the message broker
        # Closing the channel gracefully
        if channel is not None:
            channel.close()
        # For closing the connection gracefully
        if message_broker is not None:
            message_broker.close()

except Exception, ee:
        # Add code here to handle the exception, print an error, and exit gracefully
        print ee
