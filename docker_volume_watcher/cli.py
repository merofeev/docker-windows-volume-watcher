"""
A tool to notify Docker contianers about changes in mounts on Windows.
"""

import argparse
import logging

import pywintypes
from docker_volume_watcher.container_monitor import ContainerMonitor
from docker_volume_watcher.container_notifier import NotifierOptions

def main():
    """
    Parse command line arguments and start monitoring.
    """

    parser = argparse.ArgumentParser(
        description='A tool to notify Docker contianers about changes in mounts on Windows.'
    )
    parser.add_argument('container_pattern', metavar='CONTAINER_PATTERN', type=str, default='*',
                        nargs='?', help='pattern of container names to be notified (default: *)')
    parser.add_argument('host_dir_pattern', metavar='HOST_DIR_PATTERN', type=str, default='*',
                        nargs='?', help='pattern of host directories to be monitored (default: *)')

    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    parser.add_argument('-e', '--exclude',
                        help='ignore changes in files/directories matching given patterns',
                        nargs='+')
    parser.add_argument('--debounce', type=float, default=0.0,
                        help='delay container notification after change occurs by DEBOUNCE '
                             'seconds ang ignore change events in the same file during '
                             'this period')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    notifier_options = NotifierOptions(args.exclude, args.debounce)
    monitor = ContainerMonitor(args.container_pattern, args.host_dir_pattern, notifier_options)

    try:
        monitor.find_containers()
        monitor.monitor()
    except KeyboardInterrupt:
        logging.info('Got KeyboardInterrupt. Exiting...')
    except pywintypes.error:
        logging.error('Failed to contact Docker daemon. Is it running?', exc_info=True)

    monitor.unwatch_all()

if __name__ == "__main__":
    main()
