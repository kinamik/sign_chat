import datetime
import csv
import json
import time

from flask import Flask, render_template, request, redirect
from google.cloud import datastore

app = Flask(__name__)
responseData = []

datastore_client = datastore.Client()

# トップページ（ガイダンスページ）
@app.route("/", methods=['GET'])
def index():

    return render_template("index.html")

# 参加者用ページ
@app.route("/visitor/<string:pageId>", methods=['GET'])
def visitor(pageId):

    checkRes = check_pageId(pageId)
    if checkRes:
        return checkRes,400
    

    # CSVから項目取得しレスポンスに乗せる
    csv_content = read_csv("eldemsign")
    responseData = csv_content

    return render_template("visitor.html",pageId= pageId, input_from_python= responseData)

# 主催者用ページ
@app.route("/streamer/<string:pageId>", methods=['GET'])
def streamer(pageId):

    checkRes = check_pageId(pageId)
    if checkRes:
        return checkRes,400

    startDatetime = int(time.time())
    return render_template("streamer.html",pageId= pageId,startDatetime= startDatetime)

# サイン書き込み
@app.route('/sign/<string:pageId>', methods=['POST'])
def postsign(pageId):
    print(request.get_json())

    checkRes = check_pageId(pageId)
    if checkRes:
        return checkRes,400

    sign = ''

    # リクエスト内容を一文に結合、ついでに各単語がcsvに存在するかチェック
    csv_content = read_csv("eldemsign")

    for item in request.get_json():
        result = False
        for i in csv_content:
            if item in i:
                result = True
                break
        if result == False:
            return '',400
        
        sign += item
    
    # 問題なければデータストア書き込み
    store_sign(pageId,sign,int(time.time()))

    return '',200

# サイン読み込み
@app.route('/sign/<string:pageId>', methods=['GET'])
def getsign(pageId):

    checkRes = check_pageId(pageId)
    if checkRes:
        return checkRes,400

    req = request.args
    startDatetime = req.get("startDatetime")

    signs = fetch_sign(pageId,startDatetime,10)
    fetchSigns = json.dumps(signs, default=json_serial)
    return fetchSigns,200

# csv読み込み
def read_csv(filename):
    f = []
    csv_file = open("./csv/" + str(filename) + ".csv", "r", encoding="utf-8", errors="", newline="" )
    f = list(csv.reader(csv_file, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True))
    #f = csv.DictReader(csv_file, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)
    return f

# json変換時に問題があれば全部文字列で変換
def json_serial(obj):
    return obj.isoformat()


# datastore書き込み
def store_sign(pageId,sign,dt):
    entity = datastore.Entity(key=datastore_client.key('sign_' + str(pageId)))
    entity.update({
        'message': sign,
        'timestamp': dt
    })

    datastore_client.put(entity)

# datastore取得
def fetch_sign(pageId,startDatetime,limit):
    query = datastore_client.query(kind='sign_' + str(pageId))
    query.add_filter("timestamp", ">=", int(startDatetime))
    query.order = ['-timestamp']

    sign = list(query.fetch(limit=limit))
    return sign

# pageIdチェック
def check_pageId(pageId):
    if not pageId.isdigit():
        return "pageId不正 数値4桁ではありません"

    if len(pageId) != 4:
        return "pageId不正 数値4桁ではありません"

    return None
    

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
