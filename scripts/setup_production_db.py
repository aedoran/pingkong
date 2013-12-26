import sys
sys.path.append('..')

import subprocess
import argparse

from common.mongo import get_db
from ensure_indexes import add_users, ensure_collection_indexes

def main(admin_user):
    mongo_uri = subprocess.Popen('heroku config:get MONGOLAB_URI', shell=True, stdout=subprocess.PIPE).stdout.read().strip()
    db = get_db(mongo_uri)
    ensure_collection_indexes(db)
    add_users(db, [admin_user])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--admin-uid', required=True)
    parser.add_argument('--admin-name', required=True)
    args = parser.parse_args()
    admin_user = (args.admin_name, args.admin_uid, True)
    main(admin_user)
