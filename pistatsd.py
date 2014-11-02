#!/usr/bin/python
"""
This file contains pistatsd.py which will read the cpu and network interface
statistics from the Raspberry Pi and publish them to a RabbitMQ exchange
"""

import pika
import pika.exceptions
import signal
import sys
import time
import json

# Global variable that controls running the app
publish_stats = True

def stop_stats_service(signal, frame):
    """
    A signal handler, that will cause the main execution loop to stop

    :param signal: (int) A number if a intercepted signal caused this handler
                   to be run, otherwise None
    :param frame: A Stack Frame object, if an intercepted signal caused this
                  handler to be run
    :return: None
    """
    global publish_stats
    publish_stats = False

def read_cpu_utilization():
    """
    Returns a dictionary with the total uptime and idle time for the system

    :return: (dict) The system 'uptime' and 'idle' time stored in keys using
                    their respective names
    """
    uptime = open("/proc/uptime","r")
    # Read and parse out the uptime and idle time values
    x = uptime.read()
    x = x.split()
    result = {"uptime": x[0],# store uptime value from reading /proc/uptime,
              "idle": x[1]# idle value from reading /proc/uptime
             }
    return result

def read_net_throughput():
    """
    Returns a dictionary with the number of bytes each installed network
    interface has transmitted (tx) and received (rx)

    :return: (dict) A dictionary of network interfaces, where each network
             interface contains dictionaries with the transmitted and received
             bytes for the respective interface
    """
    result = dict()

    net_info = open("/proc/net/dev")
    # Parse out each network interface
    # --------------------------------
    # Since there can be multiple installed interfaces, you want to parse each
    # line in /proc/net/dev, and use the interface name as keys in the result
    for iface in net_info:
        if(iface.find(':')!=-1):#":" was found meaning an interface
            x = iface.split()#get the data in "blocks"
            result[x[0]] = {"rx": x[1],# Read bytes received from net_info,
                             "tx": x[9]# Read bytes sent from net_info
                             }
    return result

# Application Entry Point
# ^^^^^^^^^^^^^^^^^^^^^^^

# Guard try clause to catch any errors that aren't expected
try:
    #Set each of the default values
    # The message broker host name or IP address
    host = None
    # The virtual host to connect to
    vhost = "/" # Defaults to the root virtual host
    # The credentials to use
    credentials = None
    # The topic to subscribe to
    topic = None

    #parse through command line arguments and assign parameters
    #if nothing is passed, defaults as set above are used
    if sys.argv:
        for i in range(0,len(sys.argv)):
            if sys.argv[i] == "-b":
                host = sys.argv[i+1]
            elif sys.argv[i] == "-p":
                vhost = sys.argv[i+1]
            elif sys.argv[i] == "-c":
                credentials = sys.argv[i+1]
		credentials = credentials.split(':')
		username = credentials[0]
		password = credentials[1]
		credentials = pika.PlainCredentials(username, password)
            elif sys.argv[i] == "-k":
                topic = sys.argv[i+1]

    # Ensure that the user specified the required arguments
    if host is None:
        print "You must specify a message broker to connect to"
        sys.exit()

    if topic is None:
        print "You must specify a topic to subscribe to"
        sys.exit()
    # Setup signal handlers to shutdown this app when SIGINT or SIGTERM is
    # sent to this app
    signal_num = signal.SIGINT
    try:
        signal.signal(signal_num, stop_stats_service)
        signal_num = signal.SIGTERM
        signal.signal(signal_num, stop_stats_service)

    except ValueError, ve:
        print "Warning: Graceful shutdown may not be possible: Unsupported " \
                "Signal: " + signal_num    

    try:
        # Connect to the message broker using the given broker address (host)
        # Use the virtual host (vhost) and credential information (credentials),
        # if provided
        message_broker = pika.BlockingConnection(pika.ConnectionParameters(
        host,virtual_host=vhost,credentials=credentials))
        # Setup the channel and exchange
        channel = message_broker.channel()
        channel.exchange_declare(exchange='pi_utilization',type='direct')
        
        # Create a data structure to hold the stats read from the previous
        # sampling time
        last_stat_sample = {"cpu": None, "net": None}

        # Set the initial values for the last stat data structure
        last_stat_sample["cpu"] = read_cpu_utilization()
        last_stat_sample["net"] = read_net_throughput()

        # Sleep for one second
        last_sample_time = time.time()
        time.sleep(1.0)

        # Loop until the application is asked to quit
        while(publish_stats):
            # Read cpu and net stats
            current_stat_sample = {"cpu": None, "net": None}
            current_stat_sample["cpu"] = read_cpu_utilization()
            current_stat_sample["net"] = read_net_throughput()

            current_sample_time = time.time()

            # Calculate time from last sample taken
            sample_period = current_sample_time - last_sample_time

            # Setup the JSON message to send
            utilization_msg = {"cpu": None, "net": dict()}

            # Calculate CPU utilization during the sleep_time
            utilization_msg["cpu"] = 1 - ((float(current_stat_sample["cpu"]["idle"])
                                           - float(last_stat_sample["cpu"]["idle"]))
                                          /(float(current_stat_sample["cpu"]["uptime"])
                                            - float(last_stat_sample["cpu"]["uptime"])))                               

            # Calculate the throughout for each installed network interface
            # -------------------------------------------------------------
            # General Note: sample_period is the amount of time between samples, and
            # is in seconds. Therefore sample_period can be used to calculate the
            # throughput in bytes/second
            for iface in current_stat_sample["net"].keys():
                rx = ((float(current_stat_sample["net"][iface]["rx"])-
                     float(last_stat_sample["net"][iface]["rx"]))/sample_period)
                tx = ((float(current_stat_sample["net"][iface]["tx"])-
                     float(last_stat_sample["net"][iface]["tx"]))/sample_period)
                rx = int(rx)
                tx = int(tx)#truncate decimal portion (insignificant)
                
                utilization_msg["net"][iface[0:len(iface)-1]] = {"rx": rx,
                                                 "tx": tx
                                                }
            #   Publish the message (utilization_msg) in JSON format to the
            #   broker under the user specified topic.
            data = json.dumps(utilization_msg,indent=4,sort_keys=True)#put dict into JSON format
            
            channel.basic_publish(exchange = 'pi_utilization', routing_key = topic,
                                  body = data)
            #print "Sent: ", data

            # Save the current stats as the last stats
            last_stat_sample = current_stat_sample
            last_sample_time = current_sample_time

            # Sleep and then loop
            time.sleep(1.0)

    except pika.exceptions.ProbableAccessDeniedError, pade:
        print >> sys.stderr, "Error: A Probable Access Denied Error occured: " + str(pade.message)
        print "Please enter a valid virtual host in the format '-p validhost'"

    except pika.exceptions.ProbableAuthenticationError, aue:
        print >> sys.stderr, "Error: A Probable Authentication error occured: " + str(aue.message)
        print "Please enter a valid username/password in the format '-c username:password'"
        
    except pika.exceptions.AMQPConnectionError, acoe:
        print >> sys.stderr, "Error: An AMQP Connection Error occured: " + str(acoe.message)
        print "Please enter a valid RabbitMQ host name in the format '-b WabbitHost'"

    except pika.exceptions.AMQPChannelError, ache:
        print >> sys.stderr, "Error: An AMQP Channel Error occured: " + str(ache.message)
    
    except pika.exceptions.ChannelError, ce:
        print >> sys.stderr, "Error: A channel error occured: " + str(ce.message)
    except pika.exceptions.AMQPError, ae:
        print >> sys.stderr, "Error: An AMQP Error occured: " + str(ae.message)
    #General catch-all handler as last resort
    except Exception, eee:
        print >> sys.stderr, "Error: An unexpected exception occured: " + str(eee.message)
    
    finally:
        # Attempt to gracefully shutdown the connection to the message broker
        print "Application Shutting Down..."
        if channel is not None:
            channel.close()
        if message_broker is not None:
            message_broker.close()
        sys.exit()
except NameError, ne:
    print "Error: A NameError has occured: It is likely that an invalid command line"
    print "argument was passed.Please check your arguments and try again"
    print "Error message: " + ne.message
    sys.exit()
except Exception, ee:
    print "Error: An unexpected error occurred: " + ee.message
    sys.exit()
