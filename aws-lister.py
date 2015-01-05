#!/usr/bin/env python

"""
List all Amazon instances from all regions.
"""

import argparse
import boto
import boto.ec2
import logging
import os
import sys

# Logging interface object
LOGGER = logging.getLogger('AmazonLister')


def main():
    """
    Entry point.
    """
    # parse command line args
    cmd_args = parse_cmd_args()
    # configure the Logger
    verbosities = {
        'none': 100,
        'critical': 50,
        'error': 40,
        'warning': 30,
        'info': 20,
        'debug': 10}
    logging.basicConfig(
        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        level = verbosities.get(cmd_args.verbosity, 30))
    # validate configurations
    access_key_id = os.environ.get('ACCESS_KEY_ID', '')
    secret_access_key = os.environ.get('SECRET_ACCESS_KEY', '')
    if len(access_key_id) == 0 or \
            len(secret_access_key) == 0:
        sys.stderr.write(
            'Error: ACCESS_KEY_ID and SECRET_ACCESS_KEY'
            ' environment variables must be exported.\n')
        sys.exit(1)
    # collect stats
    instances = []
    for region_info in boto.ec2.regions():
        instances += \
            get_instances_from_region(
            access_key_id, secret_access_key, region_info)
    # print a table
    sys.stdout.write(
        '%-10s %-11s %-15s %-15s %-15s %-15s\n' %
        ('Region', 'ID', 'Type', 'PrivIP', 'PubIP', 'Status'))
    for instance in instances:
        priv_ip = '' if instance.private_ip_address is None \
            else instance.private_ip_address
        public_ip = '' if instance.ip_address is None \
            else instance.ip_address
        sys.stdout.write(
            '%-10s %-11s %-15s %-15s %-15s %-15s\n' %
            (instance.region_name, instance.id,
             instance.instance_type, priv_ip, public_ip,
             instance.state))


def get_instances_from_region(access_key_id, secret_access_key,
                              region_info):
    """
    Return a list of instances for the Amazon region.

    :param access_key_id: Access Key ID for Amazon API.
    :type access_key_id: string

    :param secret_access_key: Secret Access Key for Amazon API.
    :type secret_access_key: string

    :param region_info: Amazon region to connect to.
    :type region_info: instance of boto.ec2.RegionInfo

    :rtype: list of instances of boto.ec2.Instance
    """
    try:
        LOGGER.info('connecting to %s region...', region_info.name)
        connection = boto.connect_ec2(
            aws_access_key_id = access_key_id,
            aws_secret_access_key = secret_access_key,
            region = region_info)
        LOGGER.info('connected')
        instances = []
        for reservation in connection.get_all_reservations():
            for instance in reservation.instances:
                instance.region_name = region_info.name
                instances.append(instance)
        return instances
    except boto.exception.EC2ResponseError as exc:
        LOGGER.exception(exc)
        return []


def parse_cmd_args():
    """
    Parse command line arguments and return
    an object with parsed arguments.

    :rtype: object
    """
    parser = argparse.ArgumentParser(
        description = 'List Amazon EC2 instances from all regions.')
    parser.add_argument(
        '-v', '--verbosity',
        default = 'warn',
        help = 'verbosity level. Default is "info". Possible'
        ' values are:'
        ' "debug", "info", "warning", "error", "critical", "none".')
    return parser.parse_args()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
