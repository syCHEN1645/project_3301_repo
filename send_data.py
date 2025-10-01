'''
import os
import shutil
import datetime
import json
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from config import INFLUX_ORG, INFLUX_TOKEN, INFLUX_URL, INFLUX_BUCKET

def sendData(data):
    # influx client
    client = influxdb_client.InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG
    )
    
    print(type(data))
    print(f"{data}")

    if (data[0]["reading"] == "Failed"):
        print(f"Reading failed, there is no valid data to send")
        return 2

    formatted_data = influxdb_client.Point("aug20test").tag("sensor_name", "wh00-pressure").field(data[0]["unit"], data[0]["reading"]).time(datetime.datetime.utcnow(), write_precision='s')

    # send data to database process
    print(f"Sending data {data}")
    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=formatted_data)

    # for debug: record data sent in a local text file 
    d = formatted_data.to_line_protocol()
    f = open("record.txt", "a")
    f.write(d + "\n")

    print("Data is sent successfully")
    return 1

# param:
# name is name of the image without .jpg
# path is absolute path of the image
def deleteData(name, path):
    # delete original image
    # os.remove(path)
    
    # delete result from model
    # shutil.rmtree(f"processed_results/{name}.jpg")

    print(f"{name}.jpg has been deleted from {path}")
    return 1


'''

# send_data.py
import datetime
import os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET
import logging

logger = logging.getLogger("sendData")
logging.basicConfig(level=logging.INFO)

def deleteData(name, path):
    # delete original image
    # os.remove(path)
    
    # delete result from model
    # shutil.rmtree(f"processed_results/{name}.jpg")

    print(f"{name}.jpg has been deleted from {path}")
    return 1

def sendData(data):
    """
    data: either a dict or a list where data[0] is dict
    expected keys in dict:
      - oilfield (e.g. "fieldA")
      - wellhead (e.g. "WH01")
      - gauge (e.g. "gauge1")
      - reading (numeric or "Failed")
      - unit (e.g. "psi")
      - confidence (optional float 0..1)
      - timestamp (optional, ISO string or datetime)
      - sensor_name (optional)
    """
    if isinstance(data, list):
        if not data:  # empty list
            print("No data to send")
            return 2
        payload = data[0]
    elif isinstance(data, dict):
        payload = data
    else:
        print("Unsupported data format")
        return 2
    # basic validation
    if payload.get("reading") in (None, "Failed"):
        print("Reading failed, no valid data to send")
        return 2

    # prepare influx client (create per-call is simpler in processes)
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    try:
        ts = payload.get("timestamp")
        if ts is None:
            ts = datetime.datetime.utcnow()
        elif isinstance(ts, str):
            ts = datetime.datetime.fromisoformat(ts)

        point = (
            Point("gauge_readings")
            .tag("oilfield", str(payload.get("oilfield", "unknown")))
            .tag("wellhead", str(payload.get("wellhead", "unknown")))
            .tag("gauge", str(payload.get("gauge", "g1")))
            .tag("sensor_name", str(payload.get("sensor_name", "sensor")))
            .field("value", float(payload["reading"]))
            .field("status", str(payload.get("status", "ok")))
            .time(ts, WritePrecision.NS)
        )

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

        # debug: write line protocol to local file for traceability
        with open("record.txt", "a") as f:
            f.write(point.to_line_protocol() + "\n")

        logger.info(f"Sent {payload['reading']} for {payload.get('oilfield')}/{payload.get('wellhead')}/{payload.get('gauge')}")
        return 1

    except Exception as e:
        logger.exception("Failed to send data to InfluxDB")
        return 0

    finally:
        try:
            client.close()
        except:
            pass
