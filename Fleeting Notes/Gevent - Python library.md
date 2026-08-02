---
title: "Gevent - Python library"
type: Fleeting Notes
category: Programming
tags:
  - "Tech"
  - "Python"
created: "2026-07-13T08:54:00.000Z"
---

## Gevent

Gevent

Gevent is a Python library used to convert some blocking I/O code into cooperatively concurrent code.

Gevent creates greenlets. Greenlets are lightweight tasks managed by gevent. They are not OS threads or processes. Multiple greenlets usually run inside the same OS thread and share an event loop called the gevent Hub.

It is called cooperative concurrency because greenlets must yield control so that other greenlets can run.

For example, suppose three greenlets are spawned to perform tasks A, B, and C.

Task A runs first. If task A makes a database or network request, it has to wait for the response. Instead of blocking the whole OS thread, task A yields control to the gevent Hub.

The Hub then runs task B. If task B also reaches an I/O operation and waits, it yields, and the Hub runs task C.

Example flow:

Task A runs → waits for database → yields

Task B runs → waits for network → yields

Task C runs → performs work → yields

Database response arrives → task A resumes

Each greenlet completes its own full task, but they take turns whenever one of them is waiting for I/O.

Example:

~~~python
import gevent

def task(name):
    print(name, "started")
    gevent.sleep(2)
    print(name, "finished")

greenlets = [
    gevent.spawn(task, "A"),
    gevent.spawn(task, "B"),
    gevent.spawn(task, "C"),
]

gevent.joinall(greenlets)
~~~

Here, gevent.sleep() pauses only the current greenlet. It gives control back to the Hub, so another greenlet can run.

Where monkey patching comes in

Greenlets can only work concurrently when blocking operations yield control.

Normal Python functions such as time.sleep() and normal socket operations block the entire OS thread.

Example without monkey patching:

~~~python
import time
import gevent

def task(name):
    print(name, "started")
    time.sleep(2)
    print(name, "finished")

greenlets = [
    gevent.spawn(task, "A"),
    gevent.spawn(task, "B"),
    gevent.spawn(task, "C"),
]

gevent.joinall(greenlets)
~~~

Here, time.sleep() blocks the OS thread. While task A is sleeping, the Hub cannot run tasks B or C.

Monkey patching fixes this for supported blocking operations.

~~~python
from gevent import monkey
monkey.patch_all()
~~~

Monkey patching replaces supported blocking functions with gevent-aware versions.

Example:

~~~python
from gevent import monkey
monkey.patch_all()

import time
import gevent

def task(name):
    print(name, "started")
    time.sleep(2)
    print(name, "finished")

greenlets = [
    gevent.spawn(task, "A"),
    gevent.spawn(task, "B"),
    gevent.spawn(task, "C"),
]

gevent.joinall(greenlets)
~~~

After monkey patching, time.sleep() behaves cooperatively. It pauses the current greenlet and allows the Hub to run another greenlet.

So the complete flow is:

Greenlets provide cooperative tasks

↓

The Hub schedules those tasks

↓

Blocking I/O must yield to the Hub

↓

Monkey patching makes supported blocking I/O yield automatically

Monkey patching should usually happen before importing libraries such as requests, socket, or other networking libraries.

~~~python
from gevent import monkey
monkey.patch_all()

import requests
~~~

Gevent vs async

Both gevent and async code allow other tasks to run while one task is waiting for I/O.

The main difference is how the code is written.

With async code, yielding is explicit:

~~~python
async def task():
    result = await fetch_data()
    return result
~~~

The await keyword tells the event loop that this task can pause and another task can run.

With gevent, the code usually looks synchronous:

~~~python
def task():
    result = requests.get("https://example.com")
    return result
~~~

After monkey patching, the network operation yields internally while waiting, even though there is no await.

So:

Async:

~~~
Explicit yielding using async and await
~~~

Gevent:

~~~
Implicit yielding using greenlets and gevent-aware operations
~~~

Both provide concurrency for I/O-bound tasks, but gevent lets synchronous-looking code behave cooperatively.

The reason gevent is used is that greenlets waiting on gevent-aware I/O do not block the OS thread. This allows other greenlets, including the main greenlet, to continue running.

However, gevent does not prevent every type of blocking.

CPU-heavy code can still block the OS thread:

~~~python
def cpu_heavy_task():
    while True:
        calculate_something()
~~~

This code does not yield, so other greenlets may not get a chance to run.

Gevent is mainly useful for I/O-bound work such as HTTP requests, API calls, database queries, socket communication, and waiting for external services. It is not mainly used for CPU-bound parallel processing.

References:

