import json
import logging
import urllib3
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI()
es = Elasticsearch(
    "https://localhost:9200",
    http_auth=("elastic", "6pVSu1PGfUvy8v+6NJoz"),
    verify_certs=False
)
INDEX_NAME = "log-data2"

origins = [
    "http://localhost:4000",
    "http://127.0.0.1:4000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

@app.on_event("startup")
def recreate_index():
    try:
        if not es.indices.exists(index=INDEX_NAME):
            index_template = {
                "index_patterns": ["log-data1*"],
                "priority": 1,
                "template": {
                    "mappings": {
                        "properties": {
                            "timestamp": {"type": "date"},
                            "body": {
                                "properties": {
                                    "service": {"type": "keyword"},
                                    "response_time": {"type": "float"},
                                }
                            },
                        }
                    }
                }
            }

            es.indices.put_index_template(name="log_template", body=index_template)
            logging.info("Index template created.")

            es.indices.create(index=INDEX_NAME)
            logging.info(f"Index '{INDEX_NAME}' created.")
        else:
            logging.info(f"Index '{INDEX_NAME}' already exists.")

        if not is_logs_already_indexed():
            read_and_index_logs_from_file("C:\\Users\\User\\my-react-app\\data\\CRMRayanSejamLog.log")
        else:
            logging.info("Logs are already indexed. Skipping indexing.")

    except Exception as e:
        logging.error(f"Error recreating index: {e}")

def is_logs_already_indexed():
    try:
        result = es.count(index=INDEX_NAME)
        doc_count = result['count']
        logging.info(f"Current document count in index '{INDEX_NAME}': {doc_count}")
        return doc_count > 0
    except Exception as e:
        logging.error(f"Error checking document count: {e}")
        return False

def read_and_index_logs_from_file(file_path):
    def convert_to_json_string(field):
        if isinstance(field, dict):
            return json.dumps(field)
        return field

    actions = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                try:
                    log = json.loads(line.strip())
                    if 'body' in log:
                        for key, value in log['body'].items():
                            log['body'][key] = convert_to_json_string(value)
                    
                    action = {
                        "_op_type": "index",
                        "_index": INDEX_NAME,
                        "_source": log
                    }
                    actions.append(action)
                    
                    if len(actions) >= 1000:
                        bulk(es, actions)
                        actions = [] 
                        
                except json.JSONDecodeError as jde:
                    logging.error(f"JSONDecodeError: {jde} - Line: {line.strip()}")

        if actions:
            bulk(es, actions)

    except Exception as e:
        logging.error(f"Error indexing logs: {e}")

@app.get("/api/services/")
def get_services():
    body = {
        "aggs": {
            "services": {
                "terms": {
                    "field": "body.service"
                }
            }
        }
    }
    try:
        result = es.search(index=INDEX_NAME, body=body)
        logging.info(f"Aggregation result: {result}")
        if "aggregations" in result and "services" in result["aggregations"]:
            services = [{"key": bucket["key"], "doc_count": bucket["doc_count"]} for bucket in result["aggregations"]["services"]["buckets"]]
            logging.info(f"Services: {services}")
            return {"services": services}
        else:
            logging.error("No aggregations found in the result")
            return {"services": []}
    except Exception as e:
        logging.error(f"Error fetching services: {e}")
        return {"services": []}

@app.get("/api/logs/")
def get_logs(service: str = None):
    query = {"match_all": {}} if service is None else {"term": {"body.service": service}}

    body = {
        "query": query,
        "aggs": {
            "by_timestamp": {
                "date_histogram": {
                    "field": "timestamp",  
                    "calendar_interval": "hour"  
                },
                "aggs": {
                    "total_requests": {
                        "value_count": {
                            "field": "timestamp" 
                        }
                    },
                    "successful_requests": {
                        "filter": {
                            "term": {"level_name": "INFO"}  
                        },
                        "aggs": {
                            "response_time": {
                                "avg": {
                                    "field": "body.response_time"
                                }
                            }
                        }
                    },
                    "error_requests": {
                        "filter": {
                            "term": {"level_name": "ERROR"}  
                        }
                    }
                }
            }
        }
    }

    try:
        result = es.search(index=INDEX_NAME, body=body)
        logging.info(f"Aggregation result: {result}")

        aggregations = result['aggregations']['by_timestamp']['buckets']
        
        logs_data = []

        for bucket in aggregations:
            timestamp = bucket['key_as_string']
            total_requests = bucket['total_requests']['value']
            
            if total_requests == 0:
                continue
            
            # successful_requests = bucket['successful_requests']['doc_count']
            successful_response_time = bucket['successful_requests']['response_time']['value']
            error_requests = bucket['error_requests']['doc_count']

            logs_data.append({
                "timestamp": timestamp,
                "total_requests": total_requests,
                # "successful_requests": successful_requests,
                "successful_response_time": successful_response_time, 
                "error_requests": error_requests
            })

        return {"logs": logs_data}

    except Exception as e:
        logging.error(f"Error fetching logs: {e}")
        return {"logs": []}
