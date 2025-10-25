import requests
import json
import pandas as pd
import time # アクセス間隔を設けるために利用

# --- 定数設定 ---
BASE_URL = "https://note.com/api/v3/searches"
LIMIT_PER_PAGE = 20 # 1回のリクエストで取得する記事数
MAX_NOTES = 100     # 最大取得記事数 (ポートフォリオとしては100件程度で十分)
DELAY_SECONDS = 1   # リクエスト間の遅延時間 (サーバーへの負荷軽減のため)

def fetch_note_articles(keyword, max_notes=MAX_NOTES):
    """
    noteの検索APIを利用して、指定キーワードの記事を収集する関数
    """
    
    all_notes = [] # 収集した全記事を格納するリスト
    start_offset = 0 # 取得開始位置（ページネーションの開始点）
    
    print(f"キーワード: 「{keyword}」の記事を最大 {max_notes} 件収集します...")

    # 記事数が上限に達するか、最終ページに到達するまで繰り返す
    while len(all_notes) < max_notes:
        
        # 1. APIリクエストのためのパラメータを設定
        params = {
            "context": "note",
            "q": keyword,
            "size": LIMIT_PER_PAGE,
            "start": start_offset
        }

        try:
            # 2. APIにリクエストを送信
            response = requests.get(BASE_URL, params=params)
            
            # 3. ステータスコードをチェック (200以外はエラー処理へ)
            if response.status_code != 200:
                print(f"[{response.status_code}] リクエストに失敗しました。停止します。")
                break
            
            data = response.json()
            
            # 4. JSON構造から記事リスト（'contents'）を安全に取得
            notes_data = data.get("data", {}).get("notes", {})
            current_notes = notes_data.get("contents", [])
            
            # 5. 記事が取得できなかった場合の処理 (最終ページ、または検索結果ゼロ)
            if not current_notes:
                print("これ以上新しい記事が見つかりませんでした。収集を終了します。")
                break
                
            # 6. 収集した記事をリストに追加
            all_notes.extend(current_notes)
            print(f"-> {len(all_notes)} 件の記事を収集済み...")

            # 7. ページネーションの制御とループの継続チェック
            
            # 最大記事数に達した場合、超過分は削除して終了
            if len(all_notes) >= max_notes:
                all_notes = all_notes[:max_notes]
                print(f"最大収集件数 ({max_notes}件) に達しました。収集を終了します。")
                break
                
            # 次のページへ進むために start_offset を更新
            start_offset += LIMIT_PER_PAGE
            
            # アクセス間隔を設ける (マナーとアクセス制限回避のため)
            time.sleep(DELAY_SECONDS)

        except requests.exceptions.RequestException as e:
            # 通信エラーが発生した場合の処理
            print(f"通信エラーが発生しました: {e}。収集を中断します。")
            break
        except Exception as e:
            # その他の予期せぬエラー
            print(f"予期せぬエラーが発生しました: {e}。収集を中断します。")
            break
            
    return all_notes

def extract_note_data(notes_list):
    extracted_data = []
    
    for note in notes_list:
        user_info = note.get('user', {})
        
        # 'createdAt' キーが存在しない、または値が空の場合は None を設定する
        created_at_str = note.get('createdAt')
        
        data = {
            'title': note.get('name', 'N/A'),
            'url': note.get('url', 'N/A'),
            'likes': note.get('like_count', 0),
            # 修正A: created_at の抽出。空文字なら None にする
            'created_at': created_at_str if created_at_str else None,
            'creator_name': user_info.get('nickname', 'N/A'),
            'creator_url': user_info.get('url', 'N/A')
        }
        extracted_data.append(data)
        
    return extracted_data
def analyze_and_output(df, keyword):
    """
    収集データを分析し、結果を出力する
    """
    
    # --- A. データ分析: ポートフォリオでアピールする最も重要な部分 ---
    
    # 1. スキ（いいね）数に基づいた人気ランキング (Top 10)
    top_notes = df.sort_values(by='likes', ascending=False).head(10)
    
    # 2. 記事の平均値/合計値の算出
    avg_likes = df['likes'].mean()
    
    # 3. 記事の公開時期の分布 (分析の幅を見せる)
    # 欠損値(NaT)を無視して分析するためにdropna()を使用
    # latest_date = df['created_at'].dropna().max().strftime('%Y-%m-%d')
    # earliest_date = df['created_at'].dropna().min().strftime('%Y-%m-%d')
    valid_dates = df['created_at'].dropna()
    
    if len(valid_dates) > 0:
        # 有効な日付がある場合のみ、最大値と最小値をフォーマット
        latest_date = valid_dates.max().strftime('%Y-%m-%d')
        earliest_date = valid_dates.min().strftime('%Y-%m-%d')
    else:
        # 有効な日付がない場合は「N/A」などを表示
        latest_date = "N/A (日付データ欠損)"
        earliest_date = "N/A (日付データ欠損)"
    
    print("\n" + "="*50)
    print(f"【note 記事分析結果】 キーワード: 「{keyword}」")
    print("="*50)
    
    print(f"総記事数: {len(df)} 件")
    print(f"平均スキ数: {avg_likes:.1f} 件")
    print(f"取得された記事の期間: {earliest_date} 〜 {latest_date}")
    
    # --- B. 結果の出力: CSV/Excel ファイル ---
    
    # ファイル名を設定
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"note_analysis_{keyword}_{timestamp}.xlsx"
    
    try:
        # Excelファイルとして保存
        df.to_excel(output_filename, index=False)
        print("\n--- データ出力 ---")
        print(f"整形済みデータを {output_filename} に保存しました。")
    except Exception as e:
        print(f"ファイルの保存中にエラーが発生しました: {e}")

    # --- C. ランキングのターミナル表示 ---
    
    print("\n--- スキ数ランキング (Top 10) ---")
    for index, row in top_notes.iterrows():
        print(f"  {index+1}. スキ数: {row['likes']:<5} | タイトル: {row['title']}")
        print(f"     URL: {row['url']}")
        
    print("="*50)

def main():
    """
    アプリのエントリーポイント（開始点）
    """
    # ユーザーからのキーワード入力を受け付け
    keyword = input("検索したいキーワードを入力してください: ")
    if not keyword:
        print("キーワードが入力されていません。終了します。")
        return

    # 1. データ収集を実行 (ステップ3)
    notes_list = fetch_note_articles(keyword)
    df, keyword = None, None # 初期化

    if notes_list:
        print(f"\n合計 {len(notes_list)} 件の記事収集に成功しました。")
        
        # 2. データ抽出 (ステップ4-1)
        extracted_data = extract_note_data(notes_list)
        
        # 3. Pandas DataFrameへの変換 (ステップ4-2)
        df = pd.DataFrame(extracted_data)

        # 4. データ型の整形（特に日時と数値）
        # 'created_at' を日時型に変換。errors='coerce'で不正な値をNaTに変換
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        # 'likes' を数値型に変換
        df['likes'] = pd.to_numeric(df['likes'], errors='coerce').fillna(0).astype(int)

        print("\n--- データの整形が完了しました ---")
        
        # ★★★ ここで整形後のDataFrameの一部を表示して確認 ★★★
        print(df.head())
        print(f"DataFrameの列情報:\n{df.dtypes}")
        
        # ステップ5（データ分析と出力）へ続く
        analyze_and_output(df, keyword)
        # 次のステップのために、DataFrameを返すか、グローバル変数に格納する
        return df, keyword # dfとキーワードを返すように変更

        

    else:
        print("\n記事の収集に失敗または該当記事がありませんでした。")
        return None, None

if __name__ == "__main__":
    main() # 実行のみ