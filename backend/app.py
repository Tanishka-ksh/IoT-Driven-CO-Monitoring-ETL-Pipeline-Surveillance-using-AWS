from flask import Flask, jsonify
from flask_cors import CORS
import boto3
import time
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)

# Athena client
athena = boto3.client('athena', region_name='ap-south-1')

DATABASE = 'iot_processed_db'
OUTPUT_S3 = 's3://iot-query-results-tanishka-new/'

# Track acknowledged alerts to prevent re-popup
acknowledged_alerts = set()

def run_query(query, max_wait_seconds=30):
    """Submit Athena query and wait for results (with timeout)."""
    try:
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': DATABASE},
            ResultConfiguration={'OutputLocation': OUTPUT_S3}
        )
        query_id = response['QueryExecutionId']

        waited = 0
        while waited < max_wait_seconds:
            status_response = athena.get_query_execution(QueryExecutionId=query_id)
            status = status_response['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                break
            elif status in ['FAILED', 'CANCELLED']:
                reason = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
                print(f"❌ Athena query {status}: {reason}")
                return {"error": f"Query {status}: {reason}"}
            
            time.sleep(1)
            waited += 1

        if status != 'SUCCEEDED':
            print(f"⏱️ Athena query timeout after {max_wait_seconds}s")
            return {"error": "Query timeout"}

        # Fetch results
        results = athena.get_query_results(QueryExecutionId=query_id)
        rows = results['ResultSet']['Rows']
        
        if len(rows) <= 1:
            print("📭 Athena returned no data rows")
            return [] 
            
        headers = [h['VarCharValue'] for h in rows[0]['Data']]
        data = []
        for row in rows[1:]:
            item = {}
            for i, cell in enumerate(row['Data']):
                value = cell.get('VarCharValue', None)
                header = headers[i]
                
                # Try to convert to float first
                try:
                    float_val = float(value)
                    item[header] = float_val
                except (ValueError, TypeError):
                    # If conversion fails...
                    if header in ['device', 'device_id', 'alert_key']:
                        # Keep it as a string if it's an identifier
                        item[header] = value
                    else:
                        # Set to 0.0 if it's any other column (co, temp, etc.)
                        item[header] = 0.0
                        
            data.append(item)
        
        print(f"✅ Athena returned {len(data)} rows")
        return data
        
    except Exception as e:
        print(f"❌ Athena error: {str(e)}")
        return {"error": str(e)}

# ------------------- API ENDPOINTS -------------------

@app.route('/latest', methods=['GET'])
def latest():
    """Fetch the 20 latest readings per device, with a simulated 130.5 ppm alert for demo"""
    query = """
    WITH ranked AS (
        SELECT 
            device, co, smoke, temp, humidity, lpg,
            CAST(to_unixtime(ts) AS BIGINT) as ts,
            ROW_NUMBER() OVER (PARTITION BY device ORDER BY ts DESC) as rn
        FROM processed
    )
    SELECT device, device AS device_id, co, smoke, temp, humidity, lpg, ts
    FROM ranked
    WHERE rn <= 20;
    """
    data = run_query(query)

    if data and not (isinstance(data, dict) and "error" in data):
        print("✅ Using REAL Athena data for /latest (Top 20).")
        
        # Inject simulated 130.5 ppm alert for Tent 1 (demo purposes)
        simulated_alert_row = {
            "device": "b8:27:eb:bf:9d:51",
            "device_id": "b8:27:eb:bf:9d:51",
            "co": 0.1305,  # 130.5 ppm
            "smoke": 0.025,
            "temp": 28.0,
            "humidity": 40.0,
            "lpg": 0.005,
            "ts": int(time.time()),
            "alert_key": "simulated_tent1_danger_130"
        }
        data.append(simulated_alert_row)
        print(f"   🚨 DEMO: Injected 130.5 ppm alert for Tent 1.")
        
    else:
        print("❌ No Athena data available for /latest")
        # If no real data, still provide the simulated alert
        simulated_alert_row = {
            "device": "b8:27:eb:bf:9d:51",
            "device_id": "b8:27:eb:bf:9d:51",
            "co": 0.1305,
            "smoke": 0.025,
            "temp": 28.0,
            "humidity": 40.0,
            "lpg": 0.005,
            "ts": int(time.time()),
            "alert_key": "simulated_tent1_danger_130"
        }
        data = [simulated_alert_row]
        print(f"   🚨 DEMO: No real data, but injected simulated 130.5 ppm alert for Tent 1.")

    return jsonify(data)


@app.route('/co_trend', methods=['GET'])
def co_trend():
    print("📈 Using simulated CO trend for chart")
    now = datetime.utcnow()
    devices = ["b8:27:eb:bf:9d:51", "00:0f:00:70:91:0a", "1c:bf:ce:15:ec:4d"]
    data = []

    for i in range(50):
        timestamp = int((now - timedelta(minutes=50 - i)).timestamp())
        
        for device in devices:
            # Tent 1 escalates to DANGER (max 130.5 ppm = 0.1305)
            if device == "b8:27:eb:bf:9d:51":
                if i > 40:
                    base_co = random.uniform(0.120, 0.1305)  # Max 130.5 ppm
                elif i > 30:
                    base_co = random.uniform(0.080, 0.120)
                else:
                    base_co = random.uniform(0.003, 0.008)
            else:
                # Tent 2 & 3: realistic safe values
                base_co = random.uniform(0.003, 0.008)
            
            data.append({
                "ts": timestamp,
                "device": device,
                "co": round(base_co, 6)
            })

    return jsonify(data)


@app.route('/avg_metrics', methods=['GET'])
def avg_metrics():
    """Calculate average metrics across entire dataset"""
    query = """
    SELECT device,
           AVG(co) AS avg_co,
           AVG(smoke) AS avg_smoke,
           AVG(temp) AS avg_temp
    FROM processed
    GROUP BY device
    """
    data = run_query(query)
    
    if not data or (isinstance(data, dict) and "error" in data):
        print("❌ No avg_metrics data available")
        return jsonify([])
    
    return jsonify(data)


@app.route('/max_metrics', methods=['GET'])
def max_metrics():
    """Calculate maximum metrics across entire dataset"""
    query = """
    SELECT device,
           MAX(co) AS max_co,
           MAX(smoke) AS max_smoke,
           MAX(temp) AS max_temp
    FROM processed
    GROUP BY device
    """
    data = run_query(query)
    
    if not data or (isinstance(data, dict) and "error" in data):
        print("❌ No max_metrics data available")
        return jsonify([])
    
    return jsonify(data)


@app.route('/alert_counts', methods=['GET'])
def alert_counts():
    """Count alerts across entire dataset"""
    query = """
    SELECT device,
           SUM(CASE WHEN co >= 0.120 THEN 1 ELSE 0 END) AS co_alerts
    FROM processed
    GROUP BY device
    """
    data = run_query(query)
    
    if not data or (isinstance(data, dict) and "error" in data):
        print("❌ No alert_counts data available")
        return jsonify([])
    
    return jsonify(data)


@app.route('/humidity_co', methods=['GET'])
def humidity_co():
    """Analyze humidity vs CO correlation"""
    query = """
    SELECT humidity, AVG(co) AS avg_co
    FROM processed
    GROUP BY humidity
    ORDER BY humidity
    """
    data = run_query(query)
    
    if not data or (isinstance(data, dict) and "error" in data):
        print("❌ No humidity_co data available")
        return jsonify([])
    
    return jsonify(data)


@app.route('/temp_dist', methods=['GET'])
def temp_dist():
    """Get temperature distribution"""
    query = """
    SELECT temp, COUNT(*) AS count
    FROM processed
    GROUP BY temp
    ORDER BY temp
    """
    data = run_query(query)
    
    if not data or (isinstance(data, dict) and "error" in data):
        print("❌ No temp_dist data available")
        return jsonify([])
    
    return jsonify(data)


# --- Utility Endpoints ---

@app.route('/acknowledge_alert', methods=['POST'])
def acknowledge_alert():
    """Mark an alert as acknowledged so it doesn't re-popup"""
    from flask import request
    alert_key = request.json.get('alert_key')
    if alert_key:
        acknowledged_alerts.add(alert_key)
        print(f"✅ Alert acknowledged: {alert_key}")
        return jsonify({"success": True, "acknowledged": alert_key})
    return jsonify({"success": False}), 400


@app.route('/reset_alerts', methods=['POST'])
def reset_alerts():
    """Reset all acknowledged alerts (for testing)"""
    global acknowledged_alerts
    acknowledged_alerts.clear()
    print("🔄 All alerts reset")
    return jsonify({"success": True, "message": "All alerts reset"})


if __name__ == "__main__":
    app.run(debug=True)