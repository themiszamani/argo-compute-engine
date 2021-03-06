#!/usr/bin/env python
import os
import sys
from argorun import run_cmd
from argolog import init_log
from argparse import ArgumentParser
from utils import ArgoConfiguration
from utils import get_date_range
from utils import get_date_str
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime


def do_recompute(argo_exec, date, tenant, job, log):
    """
    Re-execute an a/r job for a specific date

    :param argo_exec: path to argo bin directory
    :param date: specific date for a/r job
    :param tenant: tenant name for a/r job
    :param job: job name
    :param log: logger reference
    """
    log.info("Recomputing: for tenant: %s and job: %s and date: %s", tenant, job, date)
    cmd_job_ar = [os.path.join(argo_exec, "job_ar.py"), '-d', date, '-t', tenant, '-j', job]
    run_cmd(cmd_job_ar, log)


def loop_recompute(argo_exec, date_range, tenant, job, log):
    """
    For a specific time period, loop and execute recomputations for each day

    :param argo_exec: path to argo bin directory
    :param date_range: list with all available dates included in the period
    :param tenant: tenant name
    :param job_set: list of tenant's available jobs
    :param log: logger reference
    """
    for dt in date_range:
        date_arg = get_date_str(dt)
        do_recompute(argo_exec, date_arg, tenant, job, log)


def get_mongo_collection(mongo_host, mongo_port, db, collection, log):
    """
    Returns pymongo object containing reference to the recalculation collection
    in the datastore (MongoDB)

    :param mongo_host: hostname of MongoDB server
    :param mongo_port: port number of MongoDB server
    :param db: database name to use
    :param collection: collection name to open
    :param log: logger object
    :return col: pymongo collection object
    """
    # Connect to the mongo server (host,port)
    log.info("Connecting to mongo server: %s:%s", mongo_host, mongo_port)
    client = MongoClient(str(mongo_host), int(mongo_port))
    # Connect to the database
    log.info("Opening database: %s", db)
    db = client[db]

    log.info("Opening collection: %s", collection)
    col = db[collection]
    return col


def get_recomputation(collection, rec_id, log):
    """
    Retrieves a recomputation request by id (query on datastore)

    :param collection: target datastore collection containing recomputations
    :param rec_id: specific ObjectId to retrieve
    :param log: logger object reference
    :returns: result in json format
    """

    # run the query
    result = collection.find_one({'id': rec_id})

    if result is None:
        log.error("Could not find specified Recomputation")
        raise ValueError("Recomputation not found in db")

    return result


def get_time_period(recomputation):
    """
    Return list with dates included in time period from a recomputation json object

    :param recomputation: target datastore collection containing recomputations
    :returns: list with all the dates included in the time period
    """
    start_date_str = recomputation["start_time"].split('T')[0]
    end_date_str = recomputation["end_time"].split('T')[0]
    return get_date_range(start_date_str, end_date_str)


def update_status(collection, rec_id, status, timestamp, log):
    """
    Update recomputation request status (In datastore)

    :param collection: target datastore collection containing recomputations
    :param rec_id: target recomputation's ObjectId
    :param status: new status value to be updated to
    :param timestamp: date and time to stamp the event
    :param log: logger object reference
    """

    # Update status and history
    collection.update({'id': rec_id}, {'$set': {"status": status,"timestamp": timestamp} })


def recompute(recalculation_id=None, tenant=None):
    """
    Script to execute recomputation

    :param recalculation_id: The id of the job to be recomputed
    :param tenant: tenants name
    """
    # default paths
    fn_ar_cfg = "/etc/ar-compute-engine.conf"
    argo_exec = "/usr/libexec/ar-compute/bin"
    arcomp_conf = "/etc/ar-compute"
    # Init configuration
    cfg = ArgoConfiguration(fn_ar_cfg)
    cfg.load_tenant_db_conf(os.path.join(arcomp_conf, args.tenant + "_db_conf.json"))
    # Init logging
    log = init_log(cfg.log_mode, cfg.log_file, cfg.log_level, 'argo.recompute')

    # Check recomputation
    col = get_mongo_collection(
        cfg.mongo_host, cfg.mongo_port, cfg.get_mongo_database("ar"), "recomputations", log)
    recomputation = get_recomputation(col, recalculation_id, log)
    dates = get_time_period(recomputation)

    update_status(col, recalculation_id, "running", datetime.now(), log)
    loop_recompute(argo_exec, dates, tenant, recomputation["report"], log)
    update_status(col, recalculation_id, "done", datetime.now(), log)


if __name__ == "__main__":
    # Feed Argument parser with the description of the 3 arguments we need
    # (input_file,output_file,schema_file)
    arg_parser = ArgumentParser(
        description="Execute a specific Recomputation")
    arg_parser.add_argument(
        "-i", "--id", help="recomputation id", dest="id", metavar="STRING", required="TRUE")
    arg_parser.add_argument(
        "-t", "--tenant", help="tenant owner", dest="tenant", metavar="STRING", required="TRUE")
    # Parse the command line arguments accordingly and introduce them to
    # recompute...
    args = arg_parser.parse_args()
    sys.exit(recompute(recalculation_id=args.id, tenant=args.tenant))
