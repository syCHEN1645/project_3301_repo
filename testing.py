from send_data import sendData

test_payload = {
    "oilfield": "fieldA",
    "wellhead": "WH01",
    "gauge": "gauge1",
    "reading": 123.4,
    "unit": "psi",
    "confidence": 0.95,
    "sensor_name": "cam1"
}

ack = sendData(test_payload)
print("ACK:", ack)
