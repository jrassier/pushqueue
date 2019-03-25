import argparse
import datetime
from pushqueue import Pushqueue

parser = argparse.ArgumentParser()

parser.add_argument("queueFile",        help="Full path to a message queue file. Don't put it in /tmp.")
parser.add_argument("apiKey",           help="Pushover API/application key identifying source.")
parser.add_argument("userKey",          help="Pushover user or group key identifying destination.")
parser.add_argument("notificationType", help="Nagios alert type. Usually PROBLEM or RECOVERY.")
parser.add_argument("host",             help="Name of the affected host.")
parser.add_argument("hostState",        help="State of the affected host.")
parser.add_argument("service",          help="Name of the affected service, if any.")
parser.add_argument("serviceState",     help="State of the affected service, if any.")
parser.add_argument("msg",              help="Message briefly describing the situation.")
parser.add_argument("--debug",          help="Enable debug output.",action="store_true")
args = parser.parse_args()

def logDebug( msg):
  if(args.debug):
    print("{} {}".format(datetime.datetime.now(), msg))

logDebug("Queue file:           {}".format(args.queueFile))
logDebug("API key:              {}".format(args.apiKey))
logDebug("User key:             {}".format(args.userKey))
logDebug("Notification type:    {}".format(args.notificationType))
logDebug("Host:                 {}".format(args.host))
logDebug("Host state:           {}".format(args.hostState))
logDebug("Service:              {}".format(args.service))
logDebug("Service state:        {}".format(args.serviceState))
logDebug("Message:              {}".format(args.msg))

db = Pushqueue.Database(args.queueFile)
nd = {'notificationType': args.notificationType,
      'host': args.host,
      'hostState': args.hostState,
      'service': args.service,
      'serviceState': args.serviceState,
      'msg': args.msg,
      'apiKey': args.apiKey,
      'userKey': args.userKey}
n = Pushqueue.Notification(**nd)
db.queueNotification(n)

