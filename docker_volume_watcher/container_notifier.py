"""
Exports ContainerNotifier enabling to notify containers about file changes in mounts.
"""

import logging
from os.path import relpath
import posixpath

import docker
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class ContainerNotifier(object):
    """
    Notifies container about file changes in binded host-directory.
    """

    def __init__(self, container, host_dir, container_dir):
        """
        Initialize a new instance of ContainerNotifier

        Args:
            container: Container
            host_dir (str): Host directory
            container_dir (str): Container directory
        """
        self.container = container
        self.host_dir = host_dir
        self.container_dir = container_dir

        event_handler = PatternMatchingEventHandler(ignore_directories=False)
        handler = self.__change_handler
        event_handler.on_created = handler
        event_handler.on_moved = handler
        event_handler.on_modified = handler

        self.observer = Observer()
        self.observer.schedule(event_handler, host_dir, recursive=True)
        self.observer.start()

    def __str__(self):
        return '%s -> %s:%s' % (self.host_dir, self.container.name, self.container_dir)

    def __change_handler(self, event):
        host_path = event.dest_path if hasattr(event, 'dest_path') else event.src_path
        relative_host_path = relpath(host_path, self.host_dir).replace('\\', '/')
        absolute_path = posixpath.join(self.container_dir, relative_host_path)
        self.notify(absolute_path)

    def notify(self, absolute_path):
        """
        Notify container about change in file.

        Args:
            absolute_path (str): Absolute path of changed file.
        """

        logging.info(
            'Notifying container %s about change in %s',
            self.container.name,
            absolute_path)
        try:
            permissions = self.container.exec_run(
                ['stat', '-c', '%a', absolute_path], privileged=True)
            permissions = permissions.decode('utf-8').strip()
            response = self.container.exec_run(
                ['chmod', permissions, absolute_path], privileged=True)
            if response:
                logging.info(str(response))
        except docker.errors.APIError:
            logging.error(
                'Failed to notify container %s about change in %s',
                self.container.name,
                absolute_path, exc_info=True)

    def stop(self):
        """
        Stop observing host directory.
        """

        self.observer.stop()
        self.observer.join()
