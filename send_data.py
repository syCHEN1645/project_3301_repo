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
