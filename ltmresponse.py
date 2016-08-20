#!/usr/bin/python
import cx_Oracle
from pprint import pprint
import bigsuds
import timeit
import time
from datetime import datetime
import cProfile
import sys
import logging
import conf

############## Database Functions ###############

def connect_database(username, password, hostname, port, service_name):
        try:
                db = cx_Oracle.connect(username, password,  hostname+':'+str(port)+'/'+service_name)
                return db
        except Exception:
                return

def get_db_cursor(db_name):
        cursor = db_name.cursor()
        return cursor

def execute_query(db_cursor, query):
        return db_cursor.execute(query)

def fetch_query_result(cursor):
        return cursor.fetchall()  ##returns List type

def update_db(db_cursor, query):
        try:
                db_cursor.execute(query)
                logging.info("Successfully updated the Database")
        except Exception, e:
                logging.warning("Failed to update the Database !!")

############## BIG-IP bigsuds functions ###############

def connect_f5(BIGIP_hostname, username, password):
        return bigsuds.BIGIP(BIGIP_hostname, username, password)


def get_f5_partition_list(f5_connection):
        is_Connection_Failed = 'no'
        try:
                f5_connection.Management.Partition.get_partition_list()
        except Exception:
                is_Connection_Failed = 'yes'

        return is_Connection_Failed
def f5_connection_time():
        pass

def f5_data_fetch_time():
        pass

def time_test(function):
        b1 = connect_f5('f5hostname.example.com', 'ltm-auto', 'ltm-auto')
        l = get_f5_partition_list(b1)

def log_message(message, severity):
        pass

#######################################################

if __name__ == '__main__':

        #### DB Details ####

        db_username = conf.db_username
        db_password = conf.db_password
        db_hostname = conf.db_hostname
        db_port = conf.db_port
        db_service_name = conf.db_service_name

        #### F5 Details ####

        f5_username = conf.f5_username
        f5_password = conf.f5_password

        ############## Logging Config ##############

        log_file = conf.log_file
        log_level = conf.log_level
        logging.basicConfig(filename=log_file, level=logging.INFO)

        ########################
        db_connection = connect_database(db_username, db_password, db_hostname, db_port, db_service_name)
        #print type(db_connection)
        if type(db_connection) == cx_Oracle.Connection:
                logging.info("Connection to database successfull")
                db_cursor = get_db_cursor(db_connection)
                query_db = execute_query(db_cursor, 'select LTM_DEVICE_NAME, LTM_DEVICE_ID, LTM_IP from ltm_device')
                fetch_query_list = fetch_query_result(db_cursor)  ## fetch_query_list is the query result in list format
                #print fetch_query_list
        else:
                logging.critical("Connection to database failed.. Exiting")
                sys.exit(1)
        ##################
        for tup in fetch_query_list:
                LTM_DEVICE_NAME = tup[0]
                LTM_DEVICE_ID = tup[1]

                LTM_IP = tup[2]
                if LTM_IP == "10.10.10.10" :
                        continue

                #print "Working on  : ", LTM_DEVICE_NAME
                Requested_On = time.strftime("%c")
                start_time = timeit.default_timer()
                IS_CONNECTION_FAILED = get_f5_partition_list(connect_f5(LTM_IP, f5_username, f5_password))
                end_time = timeit.default_timer()

                RESPONSE_TIME = int((end_time - start_time) * 1000) ### Response time value in milliseconds to go into the DB

                if IS_CONNECTION_FAILED == "no":
                        logging.info("Connection attempt to device "+tup[0]+" succeeded")
                else:
                        logging.critical("Connection attempt to device "+tup[0]+" failed")

                if RESPONSE_TIME > conf.response_time_threshold:
                        logging.critical("Connection time threshold reached for device "+tup[0])

                update_db(db_cursor, "insert into ltm_device_response_history(H_ID, LTM_DEVICE_ID, RESPONSE_TIME, IS_CONNECTION_FAILED) values (Ltm_Device_Response_Seq.nextval,"+str(LTM_DEVICE_ID)+","+str(RESPONSE_TIME)+","+"'"+IS_CONNECTION_FAILED+"'"+")")

        try:
                db_connection.commit()
                logging.info("Database commit succeeded")
        except Exception:
                logging.warning("Failed to commit data to the database")
