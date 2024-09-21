import json

def re_encode_line(line):
    data = json.loads(line)
    try:
        data['json_payload'] = json.loads(data['payload'])
    except ValueError:
        data['raw_payload'] = data['payload'].decode()
    del data['payload']
    return data

def re_encode():
    with open("mqtt_log_reencoded.jsonl", "w") as out_f:
        with open("mqtt_log.jsonl") as in_f:
            for line in map(re_encode_line, in_f):
                out_f.write(json.dumps(line) + "\n")

