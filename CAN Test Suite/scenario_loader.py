import csv

def load_scenario(file_path):
    scenario = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            scenario.append({
                'timestamp': float(row['timestamp']),
                'id': int(row['id'], 16),
                'data': bytes.fromhex(row['data']),
                'expected_response_id': int(row['expected_response_id'], 16) if row['expected_response_id'] else None,
                'expected_response_data': bytes.fromhex(row['expected_response_data']) if row['expected_response_data'] else None
            })
    return scenario
