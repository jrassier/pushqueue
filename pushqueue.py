import sqlite3
import datetime
import sys

from pprint import pprint
from collections import defaultdict
from pushover import Client

class Pushqueue:

  debug = True
  
  @staticmethod
  def logDebug(msg):
    if(Pushqueue.debug):
      print("{} {}".format(datetime.datetime.now(), msg))

########################################################################
  
  class Notification:
    """Represents a notification as received from our caller (nagios/icinga/whatever)"""
    def __init__(self, **kwargs):
      self.__dict__.update(kwargs)

    def printDebug(self):
      pprint(self.__dict__)

    @staticmethod
    def fromDbRecord(r):
      return Pushqueue.Notification(**r)

    def __str__(self):
      formattedMsg = ""
      # If a service is mentioned, this is a service notification.
      if(self.service != ""):
        formattedMsg = "{}: {} on {} is {}".format(self.notificationType, self.service, self.host, self.serviceState)
      # Otherwise it's a host notification.
      else:
        formattedMsg = "{}: {} is {}".format(self.notificationType, self.host, self.hostState)
      return formattedMsg

########################################################################
    
  class Alert:
    """Represents a a Pushover message as it will be sent to the user"""
    def __init__(self, title, body, apiKey, userKey, notificationIDs = None):
      self.title = title
      self.body = body
      self.apiKey = apiKey
      self.userKey = userKey
      self.notificationIDs = notificationIDs

    def printDebug(self):
      pprint(self.__dict__)

    @staticmethod
    def fromNotificationList(nl):
      # Takes a list of Notification objects and summarizes them into
      # one or more Alert objects
      
      # If we've received a single notification, the Alert title should
      # be the summary (x is y) and the body should be the message.
      
      # If there are multiple notifications, the title should be a per-
      # type count (X Problem, Y Recovery, etc) and the body should
      # contain each notification's summary, up to 1021 characters to
      # allow for a '...'
      
      results = []

      # Since we're supporting multiple source/destination keys, we have
      # to sort by source and destination key before we group the
      # Notifications together into an Alert.

      nl_sorted = defaultdict(lambda: defaultdict(list))
      for n in nl:
        nl_sorted[n.apiKey][n.userKey].append(n)

      for apiKey, sourceGroup in nl_sorted.items():
        for userKey, destGroup in sourceGroup.items():
          counts = defaultdict(int)
          body = ""
          title = ""
          ids = []
          
          if(len(destGroup) == 1):
            Pushqueue.logDebug("Formatting single-notification alert")
            n = destGroup[0]
            a = Pushqueue.Alert(str(n), n.msg, n.apiKey, n.userKey, [n.id])
            results.append(a)
          else:
            Pushqueue.logDebug("Formatting summary alert for {} notifications".format(len(destGroup)))
            for n in destGroup:
              counts[n.notificationType] += 1
              body += "{}\n".format(str(n))
              ids.append(n.id)
            
            title_l = []
            for notificationType, count in counts.items():
              title_l.append("{} {}".format(count,notificationType))
            title = ', '.join(title_l)
            
            if(len(title) > 247):
              title = title[:247] + '...'
            
            if(len(body) > 1021):
              body = body[:1021] + '...'
            
            a = Pushqueue.Alert(title, body, apiKey, userKey, ids)
            results.append(a)
      
      return results
          
    def send(self):
      Pushqueue.logDebug("Sending Alert with title [{}] and body [{}] to user key [{}] using API key [{}]".format(self.title, self.body, self.userKey, self.apiKey))
      pushoverClient = Client(self.userKey, api_token=self.apiKey)
      pushoverClient.send_message(self.body, title=self.title)

########################################################################
    
  class Database:

    def __init__(self, dbFile):
      self.conn = sqlite3.connect(dbFile)
      self.conn.isolation_level = None
      self.conn.row_factory = sqlite3.Row
      createsql = """
      CREATE TABLE IF NOT EXISTS notification
        (id integer primary key,
         notificationType text not null,
         host text not null,
         hostState text,
         service text,
         serviceState text,
         msg text,
         apiKey text,
         userKey text,
         queued datetime default current_timestamp,
         sent datetime)
      """
      cur = self.conn.cursor()
      try:
        cur.execute(createsql)
        Pushqueue.logDebug("DB init successful")
      except Exception as e:
        Pushqueue.logDebug("DB init failed: {}".format(str(e)))
      finally:
        cur.close()

    def queueNotification(self, n):
      Pushqueue.logDebug("Queueing notification of type [{}] for host [{}] in host state [{}], service [{}] in state [{}] with message [{}] to be sent by API key [{}] to user/group key [{}]".format(n.notificationType,n.host,n.hostState,n.service,n.serviceState,n.msg,n.apiKey,n.userKey))
      cur = self.conn.cursor()
      try:
        cur.execute("begin")
        cur.execute("INSERT INTO notification (notificationType,host,hostState,service,serviceState,msg,apiKey,userKey) VALUES (?,?,?,?,?,?,?,?)",(n.notificationType,n.host,n.hostState,n.service,n.serviceState,n.msg,n.apiKey,n.userKey))
        cur.execute("commit")
        Pushqueue.logDebug("Success")
        return True
      except Exception as e:
        cur.execute("rollback")
        Pushqueue.logDebug("Failed to queue notification: {}".format(str(e)))
        return False
      finally:
        cur.close()
    
    def getUnsentNotifications(self):
      notifications = []
      cur = self.conn.cursor()
      try:
        for r in cur.execute("SELECT id, notificationType, host, hostState, service, serviceState, msg, apiKey, userKey, queued FROM notification WHERE sent IS NULL ORDER BY queued ASC"):
          n = Pushqueue.Notification.fromDbRecord(r)
          notifications.append(n)

        return notifications
      except Exception as e:
        Pushqueue.logDebug("Failed to retrieve unsent notifications: {}".format(str(e)))
      finally:
        cur.close()
      
    def markNotificationsAsSent(self, notificationIDs):
      Pushqueue.logDebug("Marking notifications {} as sent".format(notificationIDs))
      idTuples = [(i,) for i in notificationIDs]
      cur = self.conn.cursor()
      try:
        cur.execute("begin")
        cur.executemany("UPDATE notification SET sent = current_timestamp WHERE id = ?",idTuples)
        cur.execute("commit")
        Pushqueue.logDebug("Success")
        return True
      except Exception as e:
        cur.execute("rollback")
        Pushqueue.logDebug("Failed: {}".format(str(e)))
        return False
      finally:
        cur.close()      
