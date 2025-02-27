import argparse
import os
import sys

import colorama

from .list import get_latest
from .fetch import get_files
from .verify import verify_directory
from ._display import display, error, warn

def bright(s, color=colorama.Fore.WHITE):
    s = ( colorama.Style.BRIGHT + color + s
            + colorama.Style.RESET_ALL + '\n' )
    sys.stdout.write(s)
    sys.stdout.flush()


def get_images(bucket_name, release_tag):
    get_files(bucket_name, release_tag, dest='images')
    print()
    verify_directory('images',
            checksum=f'md5sums_{release_tag}',
            manifest=f'file_manifest_{release_tag}.yml')

def get_scripts(bucket_name, release_tag):
    #TODO: why don't scripts have checksums?
    get_files(bucket_name, 'unpacker', dest='.')


def get_docker(bucket_name):
    get_files(bucket_name, 'docker')
    print()
    verify_directory('docker',
            checksum=f'md5checksum',
            require_manifest=False,
            strict_checksum=False)  #TODO: BAD JUJU


def get_rhel(bucket_name):
    get_files(bucket_name, 'redhat-iso', dest='rhel')
    print()
    verify_directory('rhel',
            checksum=f'md5checksum',
            require_manifest=False,
            strict_checksum=False)  #TODO: BAD JUJU


#it's assumed that colorama.init() is called before this function
def bootstrap(bucket_name, *, release_tag=None,
        download_docker=True, download_rhel=True):

    if release_tag is None:
        release_tag = get_latest(bucket_name)

    cur_dir = os.getcwd()
    os.makedirs('opal_artifacts', exist_ok=True)
    os.chdir('opal_artifacts')

    try:
        bright('Downloading and Verifying OPAL artifacts')
        get_images(bucket_name, release_tag)
        print()

        bright('Downloading and Verifying installation scripts')
        get_scripts(bucket_name, release_tag)
        if download_docker:
            print()
            bright('Downloading and Verifying docker')
            get_docker(bucket_name)
        if download_rhel:
            print()
            bright('Downloading and Verifying RHEL-8')
            get_rhel(bucket_name)

    finally:
        os.chdir(cur_dir)

    bright('SUCCESS', colorama.Fore.GREEN)


def main():
    parser = argparse.ArgumentParser('download_opal_artifacts')
    parser.add_argument("bucket_name", help="name of s3 bucket")
    parser.add_argument("release_tag", nargs="?", default=None,
            help="OPAL release tag to be downloaded, in YYYY.MM.DD form")
    parser.add_argument("--no-docker", default=False, action="store_true",
            help="Do not download binaries for docker")
    parser.add_argument("--no-rhel", default=False, action="store_true",
            help="do not download a vetted RHEL8 ISO image")

    args =  parser.parse_args()
    with display():
        try:
            bootstrap(args.bucket_name, release_tag=args.release_tag,
                download_docker = not args.no_docker,
                download_rhel = not args.no_rhel)
        except Exception as e:
            error(f'FAILURE: {str(e)}')
            sys.exit(1)


if __name__ == '__main__':
    main()
