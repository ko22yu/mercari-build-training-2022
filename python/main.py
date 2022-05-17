import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
# 追加
import os  # os.path()
import json  # json.load(), json.dump()
import sqlite3  # SQLiteの操作
import hashlib  # hash256でhash化
import os  # os.path.splitext(), os.path.basename()

# ----- DB --------------------------------------
def create_table():
    db_name = "../db/mercari.sqlite3"
    # DBを作成する(すでに作成されていたらこのDBに接続する)
    conn = sqlite3.connect(db_name, check_same_thread = False)
    # SQLiteを操作するためのカーソルを作成
    cur = conn.cursor()

    # テーブルの作成
    # CREATE TABLE IF NOT EXISTS tablename(...) とすれば
    # テーブルが存在しなければテーブルを作成してくれる
    cur.execute(
        "create table if not exists items (id integer primary key autoincrement, name string, category string, image string);"
    )
    # データベースへコミットして、変更を反映させる
    conn.commit()


create_table()

# ----------------------------------------------
app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "image"
origins = [ os.environ.get('FRONT_URL', 'http://localhost:3000') ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)

# -----------------------------------------------------
def add_item_to_json(new_item, file_name = "items.json"):
    # 初期化
    items_dict = {"items" : []}

    # items.jsonからすでにあるデータを取り出す
    if os.path.isfile(file_name):  # items.jsonが存在するなら
        # ファイルを読んでいる最中に何かエラーが起きて異常終了することになってもファイルを開いたままにしない
        with open(file_name, "r") as f:
            # JSONファイルを辞書として読み込む
            items_dict = json.load(f)

    # items.jsonに新しく登録された商品を書き込む
    with open(file_name, "w") as f:
        items_dict["items"].append(new_item)
        # 辞書をJSONファイルとして保存する
        json.dump(items_dict, f)

def get_item_from_json():
    # 初期化
    items_dict = {"items" : []}

    file_name = "items.json"
    # items.jsonのデータを読み込む
    if os.path.isfile(file_name):  # items.fileが存在するなら
        with open(file_name, "r") as f:
            # JSONファイルを辞書として読み込む
            items_dict = json.load(f)
    return items_dict


def add_item_to_db(new_item):
    db_name = "../db/mercari.sqlite3"
    # DBを作成する(すでに作成されていたらこのDBに接続する)
    conn = sqlite3.connect(db_name, check_same_thread = False)
    # SQLiteを操作するためのカーソルを作成
    cur = conn.cursor()

    # 新しい商品をデータベースに追加する
    cur.execute("insert into items(name, category, image) values (?, ?, ?)", new_item)
    # データベースへコミットして、変更を反映させる
    conn.commit()

    # DBとの接続を閉じる
    conn.close()


def get_item_from_db():
    db_name = "../db/mercari.sqlite3"
    # DBを作成する(すでに作成されていたらこのDBに接続する)
    conn = sqlite3.connect(db_name, check_same_thread = False)
    # SQLiteを操作するためのカーソルを作成
    cur = conn.cursor()

    # データを表示させる
    cur.execute("select * from items;")

    # fetchall(): 中身を全て取得する
    content_in_db = cur.fetchall()

    # DBとの接続を閉じる
    conn.close()

    return content_in_db


def search_item_from_db(keyword):
    db_name = "../db/mercari.sqlite3"
    # DBを作成する(すでに作成されていたらこのDBに接続する)
    conn = sqlite3.connect(db_name, check_same_thread = False)
    # SQLiteを操作するためのカーソルを作成
    cur = conn.cursor()

    # データを表示させる
    cur.execute("select * from items where name like ?;", ("%{}%".format(keyword), ))

    # fetchall(): 中身を全て取得する
    found_item = cur.fetchall()

    # DBとの接続を閉じる
    conn.close()

    return found_item


def get_hash(str):
    hash_value = hashlib.sha256(str.encode()).hexdigest()
    return hash_value


def save_image(input_image_path, output_image_path):
    with open(input_image_path, "rb") as f:
        image_data = f.read()
    with open(output_image_path, "wb") as f:
        f.write(image_data)


def get_item_information_from_db(item_id):
    db_name = "../db/mercari.sqlite3"
    # DBを作成する(すでに作成されていたらこのDBに接続する)
    conn = sqlite3.connect(db_name, check_same_thread = False)
    # SQLiteを操作するためのカーソルを作成
    cur = conn.cursor()

    # item_idと一致する商品の情報を表示させる
    cur.execute("select * from items where id = ?;", (item_id, ))

    # fetchall(): 中身を全て取得する
    content_in_db = cur.fetchall()

    # DBとの接続を閉じる
    conn.close()

    return content_in_db


# ["jacket","fashion","..."]
# -> {"name": "jacket", "category": "fashion", "image": "..."}
def transform_list_into_dict(list):
    column = {0: "id", 1: "name", 2: "category", 3: "image"}
    dict = {}
    for i, l in enumerate(list):
        dict[column[i]] = l
    return dict


# ----- endpoints -----------------------------------
@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = File(...)):
    # new_item = {"name": name, "category": category}
    # add_item_to_json(new_item)

    input_image_path = "images/" + image.filename
    # 拡張子なしのファイル名をハッシュ化する
    output_image_name = str(get_hash(os.path.splitext(os.path.basename(image.filename))[0])) + ".jpg"
    output_image_path = "images/" + output_image_name

    new_item = (name, category, output_image_name)
    add_item_to_db(new_item)
    save_image(input_image_path, output_image_path)

    logger.info(f"Receive item: {name}, {category}, {image}")
    return {"message": f"item received: {name}, {category}, {image}"}


@app.get("/items")
def get_item():
    all_item_list = get_item_from_db()

    # [[12,"jacket","fashion", ...],[...], ...]
    # -> {"items": [{"name": "jacket", "category": "fashion"}, ...]}
    all_item_dict = {"items": []}
    for item_list in all_item_list:
        all_item_dict["items"].append(transform_list_into_dict(item_list))

    return all_item_dict


@app.get("/items/{item_id}")
def get_item_information(item_id):
    item_information_list = get_item_information_from_db(item_id)

    # [["jacket","fashion", ...]]
    # -> {"name": "jacket", "category": "fashion", "image": "..."}
    item_information_dict = transform_list_into_dict(item_information_list[0])
    del item_information_dict["id"]
    return item_information_dict


@app.get("/image/{items_image}")
async def get_image(items_image):
    # Create image path
    image = images / items_image

    if not items_image.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)


# $ curl -X GET 'http://127.0.0.1:9000/search?keyword=jacket'
# -> この場合、search_item関数の引数のkeywordにはjacketが入る
@app.get("/search")
# Flaskではクエリパラメータをキャプチャまたは指定することはできない
# ex) @app.get("/search?keyword=<keyword>")とはできない
def search_item(keyword: str = None):
    found_item_list = search_item_from_db(keyword)

    # [[12,"jacket","fashion", ...],[...], ...]
    # -> {"items": [{"name": "jacket", "category": "fashion"}, ...]}
    found_item_dict = {"items": []}
    for item_list in found_item_list:
        found_item_dict["items"].append(transform_list_into_dict(item_list))

    return found_item_dict
