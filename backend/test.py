from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch(
    "https://localhost:9200",
    http_auth=("elastic", "6pVSu1PGfUvy8v+6NJoz"),
    verify_certs=False
)
try:
   
    indices = es.cat.indices(format="json")  

    
    index_names = [index['index'] for index in indices]

    
    for index_name in index_names:
        if index_name != "log-data2":  
            try:
                es.indices.delete(index=index_name)
                print(f"Index '{index_name}' deleted.")
            except Exception as e:
                print(f"Error deleting index '{index_name}': {e}")
        else:
            print(f"Skipping index '{index_name}' (preserved).")

except Exception as e:
    print(f"Error retrieving indices: {e}")
