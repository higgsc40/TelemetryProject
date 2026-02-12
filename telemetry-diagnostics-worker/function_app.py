import azure.functions as func
import time
import json
import logging
from collections import Counter


failure_counts = Counter()
revision_counts = Counter()
firmware_counts = Counter()


app = func.FunctionApp()

@app.function_name(name="telemetry_diagnostics_worker")
@app.event_hub_message_trigger(arg_name="azeventhub", event_hub_name="xxxxxxxxx",
                               connection="EVENTHUBCONNECTION", consumer_group="diagnostics", cardinality="many") 
def telemetry_diagnostics_worker(azeventhub: func.EventHubEvent):
    start_time = time.time()
    logging.info(f"Received batch with {len(azeventhub)} events")

    for event in azeventhub:
           try:
               body = event.get_body().decode('utf-8')
               message = json.loads(body)

               failure = classify_failure(message)

               failure_counts[failure] += 1
               revision_counts[message["hwRevision"]] += 1
               firmware_counts[message["firmwareVersion"]] += 1
    
               logging.info('Hardware failure found',
                extra = {
                        "device_id": message["deviceId"],
                        "failure": failure,
                        "firmware_version": message["firmwareVersion"],
                        "timestamp": message["timestamp"],
                        "hw_revision": message["hwRevision"],
                        "reset_reason": message["resetReason"],
                        "vcore_mv": message["vcoreMv"],
                        "vcore_ma": message["vcoreMa"],
                        "soc_temp_c": message["socTempC"],
                        "fan_rpm": message["fanRpm"],
                        "uptime_ms": message["uptimeMs"]
                        
                    }
                )
           except Exception as e:
               logging.error(f"Error processing event: {e}")
    processing_time_ms = int((time.time() - start_time) * 1000)
logging.info( "Batch diagnostics summary", 
                extra={ 
                    "total_events": len(azeventhub),
                    "processing_time_ms": processing_time_ms,
                    "failure_counts": dict(failure_counts),
                    "hardware_revisions": dict(revision_counts),
                    "firmware_versions": dict(firmware_counts) 
                    }
)
