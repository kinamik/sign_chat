import datetime
import csv
import json

from flask import Flask, render_template, request, redirect
from google.cloud import datastore

app = Flask(__name__)
responseData = []

datastore_client = datastore.Client()

# datastore書き込み
def store_sign(sign,dt):
    entity = datastore.Entity(key=datastore_client.key('sign'))
    entity.update({
        'message': sign,
        'timestamp': dt
    })

    datastore_client.put(entity)

# datastore取得
def fetch_sign(limit):
    query = datastore_client.query(kind='sign')
    query.order = ['-timestamp']

    sign = list(query.fetch(limit=limit))

    return sign

@app.route("/", methods=['GET'])
def index():

    # CSVから項目取得しレスポンスに乗せる
    csv_content = read_csv("eldemsign")
    responseData = csv_content
    print(responseData)

    return render_template("index.html",input_from_python= responseData)

@app.route('/sign', methods=['POST'])
def post():
    print(request.get_json())

    sign = ''

    # リクエスト内容を一文に結合、ついでに各単語がcsvに存在するかチェック
    csv_content = read_csv("eldemsign")

    for item in request.get_json():
        print(item)
        result = False
        for i in csv_content:
            print(i)
            if item in i:
                print('true')
                result = True
                break
        if result == False:
            print('err')
            return '',400
        
        sign += item
    
    # 問題なければデータストア書き込み
    store_sign(sign,datetime.datetime.now(tz=datetime.timezone.utc))
    # 取得テスト
    aweawe = fetch_sign(10)
    print(aweawe)
    fetchSign = json.dumps(aweawe, default=json_serial)
    

    return fetchSign,200

def read_csv(filename):
    f = []
    csv_file = open("./csv/" + str(filename) + ".csv", "r", encoding="utf-8", errors="", newline="" )
    f = list(csv.reader(csv_file, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True))
    #f = csv.DictReader(csv_file, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)
    return f

# json変換時に問題があれば全部文字列で変換
def json_serial(obj):
    return obj.isoformat()


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
