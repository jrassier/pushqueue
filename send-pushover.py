import argparse
import datetime
from pushqueue import Pushqueue

parser = argparse.ArgumentParser()
parser.add_argument("queueFile",        help="Full path to a message queue file. Don't put it in /tmp.")
parser.add_argument("--debug",          help="Enable debug output.",action="store_true")
args = parser.parse_args()

def logDebug( msg):
  if(args.debug):
    print("{} {}".format(datetime.datetime.now(), msg))

logDebug("Queue file: {}".format(args.queueFile))

Pushqueue.debug = args.debug
db = Pushqueue.Database(args.queueFile)
unsent = db.getUnsentNotifications()

alerts = Pushqueue.Alert.fromNotificationList(unsent)
for a in alerts:
  a.send()
  db.markNotificationsAsSent(a.notificationIDs)
