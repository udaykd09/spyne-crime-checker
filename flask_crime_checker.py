
import datetime
import requests, json
from collections import Counter
from flask import Flask, request, Response
SPOT_CRIME_URL = "https://api.spotcrime.com/crimes.json"
JSON_CONTENT = 'application/json'
app = Flask(__name__)

def time_in_range(start, end, x):
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

def generate_time_ranges(crimes):
    # extract time categories
    range = {
        "12:01am-3am": 0,
        "3:01am-6am": 0,
        "6:01am-9am": 0,
        "9:01am-12noon": 0,
        "12:01pm-3pm": 0,
        "3:01pm-6pm": 0,
        "6:01pm-9pm": 0,
        "9:01pm-12midnight": 0
    }

    # 0001-0300
    s1 = datetime.time(0, 0, 1)
    e1 = datetime.time(3, 0, 0)

    # 0301-0600
    s2 = datetime.time(3, 0, 1)
    e2 = datetime.time(6, 0, 0)

    # 0601-0900
    s3 = datetime.time(6, 0, 1)
    e3 = datetime.time(9, 0, 0)

    # 0901-1200
    s4 = datetime.time(9, 0, 1)
    e4 = datetime.time(12, 0, 0)

    # 1201-1500
    s5 = datetime.time(12, 0, 1)
    e5 = datetime.time(15, 0, 0)

    # 1501-1800
    s6 = datetime.time(15, 0, 1)
    e6 = datetime.time(18, 0, 0)

    # 1801-2100
    s7 = datetime.time(18, 0, 1)
    e7 = datetime.time(21, 0, 0)

    # 2101-0000
    s8 = datetime.time(21, 0, 1)
    e8 = datetime.time(0, 0, 0)

    for crime in crimes:
        ts = datetime.datetime.strptime(crime['date'], "%m/%j/%y %H:%M %p").time()

        if time_in_range(s1, e1, ts):
            range["12:01am-3am"] += 1
        elif time_in_range(s2, e2, ts):
            range["3:01am-6am"] += 1
        elif time_in_range(s3, e3, ts):
            range["6:01am-9am"] += 1
        elif time_in_range(s4, e4, ts):
            range["9:01am-12noon"] += 1
        elif time_in_range(s5, e5, ts):
            range["12:01pm-3pm"] += 1
        elif time_in_range(s6, e6, ts):
            range["3:01pm-6pm"] += 1
        elif time_in_range(s7, e7, ts):
            range["6:01pm-9pm"] += 1
        elif time_in_range(s8, e8, ts):
            range["9:01pm-12midnight"] += 1

    return range

def get_street(address):
    if " ST" in address:
        if " OF " in address:
            return address.rsplit(" OF ")[1]
        elif "BLOCK " in address:
            return address.rsplit("BLOCK ")[1]
        else:
            return address

def get_top_streets(crimes):
    streets = Counter()
    for crime in crimes:
        c = crime['address']
        if " ST " in c and " ST" in c.rsplit(" ST ")[1]:
            streets[get_street(c.rsplit(" & ")[0])] += 1
            streets[get_street(c.rsplit(" & ")[1])] += 1
        elif " ST" in c:
            if " & " in c:
                streets[get_street(crime['address'].rsplit(" & ")[0])] += 1
            else:
                streets[get_street(crime['address'])] += 1

    return sorted(streets, key=streets.get, reverse=True)[:3]

def get_crime_type(crimes):
    crime_types = {}
    for crime in crimes:
        crime_type = crime['type']
        if crime_type in crime_types:
            crime_types[crime_type] += 1
        else:
            crime_types[crime_type] = 1
    return crime_types

def aggregator(dump):
    report = {}

    # Get Total crime count
    report['total_crime'] = len(dump['crimes'])

    # Get Crime type count and Top crime cities
    report['crime_type_count'] = get_crime_type(dump['crimes'])

    # Select top 3 streets
    report['the_most_dangerous_streets'] = get_top_streets(dump['crimes'])

    # Get event time report
    report['event_time_count'] = generate_time_ranges(dump['crimes'])

    return json.dumps(report, indent=4)


def get_report(lat, lon, radius):
    lat = lat or 1
    lon = lon or 1
    radius = radius or 0.02
    params = {'lat': lat, 'lon': lon, 'radius': radius, 'key': '.'}
    external_resp = requests.get(url=SPOT_CRIME_URL, params=params)
    report = aggregator(json.loads(external_resp.text))
    return report

@app.route('/checkcrime')
def checkcrime():
    lat = request.args.get('lat') or 1
    lon = request.args.get('lon') or 1
    radius = request.args.get('radius') or 0.02
    report = get_report(lat, lon, radius)
    resp = Response(report, status=200, mimetype=JSON_CONTENT)
    return resp

if __name__ == '__main__':
    print("Starting Server --> localhost:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)
