import requests
import json
import pandas as pd

# 1. パラメータの設定
search_keyword = "ポートフォリオ"
limit_per_page = 20 # 1回の取得件数
start_offset = 0    # 取得開始位置 (0: 1ページ目)

# 2. エンドポイントURLとパラメータの準備
# 特定したエンドポイント構造を使用
url = "https://note.com/api/v3/searches"
params = {
    "context": "note",
    "q": search_keyword,
    "size": limit_per_page,
    "start": start_offset
}

# 3. APIにリクエストを送信
response = requests.get(url, params=params)

# 4. ステータスコードの確認 (200なら成功)
print(f"ステータスコード: {response.status_code}")

if response.status_code == 200:
   # 5. 応答データをJSONとして取得
  data = response.json()
  # 検索結果の記事リストを取得
  # note APIの正しい構造に合わせて "notes" の中の "contents" を取得する
  notes_list = data.get("data", {}).get("notes", {}).get("contents")
    
# 6. データの構造を確認
  if notes_list and len(notes_list) > 0:
    # リストが存在し、かつ要素が1つ以上ある場合のみ処理を行う
      first_note = notes_list[0]
    
    # 取得したい情報があるか確認
      print("\n--- 取得データの例 (最初の記事) ---")
      print(f"タイトル: {first_note.get('name')}")
      print(f"URL: {first_note.get('url')}")
      print(f"スキの数: {first_note.get('likeCount')}")
      print(f"投稿者: {first_note.get('user', {}).get('nickname')}")
    
  else:
    # notes_listが空の場合（検索結果なし）の処理
    print("\n検索結果が見つかりませんでした。")
    print("キーワードを変えて再試行してください。")

else:
    print("\nAPIリクエストに失敗しました。URLまたはパラメータを確認してください。")