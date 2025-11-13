import os
from flask import Flask, request, render_template, send_file, redirect, url_for
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# ★ Cドライブから基準ファイルAを読み込むパスを設定 ★
# WSLの/mnt/c/temp_data/base_file_a.csv にアクセスします。
# このファイルは、アプリ起動時に読み込まれ、整形処理の基準となります。
BASE_FILE_PATH = '/mnt/c/temp_data/base_file_a.csv'

# 基準となるDataFrameと列リストをグローバルに保持
try:
    # 基準ファイルAを読み込み、列情報のみを取得
    df_base = pd.read_csv(BASE_FILE_PATH, nrows=0) 
    BASE_COLUMNS = df_base.columns.tolist()
    print(f"基準ファイルA ({BASE_FILE_PATH}) を正常に読み込みました。")
    print(f"基準列: {BASE_COLUMNS}")
except FileNotFoundError:
    # ファイルが見つからない場合は、仮の列リストを設定 (デバッグ用)
    BASE_COLUMNS = ['ID', 'Name', 'Value', 'Date'] 
    print(f"警告: 基準ファイル'{BASE_FILE_PATH}'が見つかりません。ダミーの列を使用します。")
except Exception as e:
    print(f"基準ファイルの読み込み中に予期せぬエラーが発生しました: {e}")
    BASE_COLUMNS = ['ID', 'Name', 'Value', 'Date'] 


@app.route('/')
def index():
    """ファイルアップロードフォームを表示するルート"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """アップロードされたファイルを処理し、ダウンロードさせるルート"""
    # 1. ファイルの存在チェック
    if 'file' not in request.files or request.files['file'].filename == '':
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    try:
        # 2. ファイルBの読み込み
        # ファイルの拡張子に応じて読み込み関数を切り替える
        if file.filename.endswith('.csv'):
            # エンコーディングエラーを避けるため、utf-8-sigを試す
            try:
                df_uploaded = pd.read_csv(file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df_uploaded = pd.read_csv(file, encoding='shift_jis')
        elif file.filename.endswith(('.xlsx', '.xls')):
            df_uploaded = pd.read_excel(file)
        else:
            return "対応していないファイル形式です (CSV, Excelのみ)", 400

        # 3. Pandasによる整形処理
        df_reformed = reshape_data(df_uploaded)

        # 4. 整形済みデータをメモリ内のバッファに書き出し
        output = BytesIO()
        # ダウンロード用にCSV形式で書き出し (Excelで開きやすいようutf-8-sig推奨)
        df_reformed.to_csv(output, index=False, encoding='utf-8-sig') 
        output.seek(0) # バッファの先頭に戻る
        
        # 5. ファイルとしてクライアントに送信 (ダウンロード)
        return send_file(
            output, 
            mimetype='text/csv', 
            as_attachment=True,
            download_name='整形済みデータ.csv' 
        )
        
    except Exception as e:
        # 処理中に発生したエラーを表示
        return f"ファイルの処理中にエラーが発生しました: {e}", 500

def reshape_data(df_uploaded: pd.DataFrame) -> pd.DataFrame:
    """
    アップロードされたDataFrameを、基準の列構成 (BASE_COLUMNS) に合わせて整形するロジック。
    """
    
    # 実際のマッピングロジックに合わせて調整してください
    # 例: アップロードファイルにある列名 -> 基準ファイルAの列名
    column_mapping = {
        '顧客ID': 'ID',
        '商品名': 'Name',
        '数量': 'Value'
        # 実際のマッピングをここに追加
    }
    
    # 1. 列名の変更
    df_reformed = df_uploaded.rename(columns=column_mapping)

    # 2. 必要な列の選択と順序の調整
    
    # 基準列に含まれる列を抽出
    cols_to_keep = [col for col in BASE_COLUMNS if col in df_reformed.columns]
    
    # 基準列に存在しないが、アップロードファイルにある列は削除される
    df_final = df_reformed[cols_to_keep] 
    
    # 3. 基準列に存在し、アップロードファイルにない列は空(None)で追加
    for col in BASE_COLUMNS:
        if col not in df_final.columns:
            df_final[col] = None 
            
    # 4. 最終的に基準の列順に並べ替える
    df_final = df_final[BASE_COLUMNS]

    # 必要に応じてデータ型変換やクリーニング処理を追加できます
    # 例: df_final['ID'] = pd.to_numeric(df_final['ID'], errors='coerce')

    return df_final


# DockerのCMDでGunicornを使うため、if __name__ == '__main__': は使用しません。
# ローカルでテストしたい場合は以下をコメントアウト解除して実行できます。
# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)