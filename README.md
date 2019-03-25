# Pushqueue

This is a library and set of scripts that allow Nagios, Icinga or something else that operates in a similar fashion to queue up Pushover alerts to be sent at an interval. If multiple notifications are going to the same destination, they are summarized and sent as 
one.

* **pushqueue.py** - Does the heavy lifting
* **queue-pushover.py** - Enqueues a notification. Your Nagios/Icinga/whatever notification script should call this.
* **send-pushover.py** - Sends all queued notifications as Pushover alerts, summarizing as appropriate.

Whatever user you run these scripts as will need to be able to read and write one file at a configurable path in order to store the notification queue. This file probably shouldn't reside in a temporary directory.
