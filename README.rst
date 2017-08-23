Docker Windows Volume Watcher
==============================
This script monitors directory bindings of Docker containers on Windows hosts and notifies containers about file changes.

The script aims to be workaround for the problem of file change events propagation on Windows hosts. Due to limitations of CIFS implementation in Linux kernel, file change events in mounted folders of host are not propagated to container by Docker for Windows. This problem renders watch mode of modern frameworks (e.g. Jekyll, ng-cli, etc.) development servers useless, since containers are not notified about file changes. This problem is described on `Docker Community Forums <https://forums.docker.com/t/file-system-watch-does-not-work-with-mounted-volumes/12038>`_.

Installation
------------
This script can be installed with pip (both Python 2 & 3 are supported).

.. code:: bat

    pip install docker-windows-volume-watcher


Usage
-----
Monitor all directory bindings of all containers. The script will listen for container start/stop events and notify all running containers about file changes.

.. code:: bat

    docker-volume-watcher


Monitor only bindings of container ``container_name``.

.. code:: bat

    docker-volume-watcher container_name


Monitor only binding of ``container_name`` to host directory ``C:\some\directory``.


.. code:: bat

    docker-volume-watcher container_name C:\some\directory


You can also specify wildcards with ``*`` and ``?`` characters. For example: monitor only bindings of containers with names containing `myproject` to directories starting with ``C:\project\folder\``.

.. code:: bat

    docker-volume-watcher *myproject* C:\project\folder\*


Use flag ``-v`` to enable verbose output: the script will report start/stop events of eligible containers and print all detected file changes.

Limitations
------------
* The script doesn't propagate to container file deletion events.
* The script requires ``stat`` and ``chmod`` utils to be installed in container (this should be true by default for the most of containers).

Implementation details
-----------------------
The script uses ``watchdog`` package to observe file change events of the host directory. Once file change event is fired the script reads file permissions of changed file (using `stat` util) and rewrites file permissions with the same value (using ``chmod`` util) thus triggering inotify event inside container.

"Rewrite file permissions approach" was used instead of updating file last modified time with ``touch`` util. Since touching will cause event loop: touch will trigger file change event in Windows, script will handle this event and touch file again, etc.
