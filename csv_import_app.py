import os
from flask import Flask, request, render_template, send_file, redirect, url_for
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# ★ Cドライブから基準ファイルAを読み込むパスを設定 ★
# WSLの/mnt/c/temp_data/base_file_a.csv にアクセスします。
# このファイルは、アプリ起動時に読み込まれ、整形処理の基準となります。
#ローカル用
# BASE_FILE_PATH = '/app/config/base_file_a.csv'

# デプロイ用
BASE_FILE_PATH = 'config/base_file_a.csv'

# 基準となるDataFrameと列リストをグローバルに保持
try:
    # 基準ファイルAを読み込み、列情報のみを取得
    df_base = pd.read_csv(BASE_FILE_PATH, encoding='utf-8-sig')
    print(f"基準ファイルA ({BASE_FILE_PATH}) を正常に読み込みました。")
except Exception as e:
    print(f"基準ファイルの読み込み中に予期せぬエラーが発生しました: {e}")


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
            download_name='双葉店.csv' 
        )
        
    except Exception as e:
        # 処理中に発生したエラーを表示
        return f"ファイルの処理中にエラーが発生しました: {e}", 500

def reshape_data(df_uploaded: pd.DataFrame) -> pd.DataFrame:
    """
    アップロードされたDataFrame (import_file_df) を使用して、
    基準DataFrame (base_file_df) の特定の位置の値を置き換えるロジック。
    """
    
    # ----------------------------------------------------
    # 1. 基準ファイルA (base_file_df) を再読み込み
    #    ※ グローバル変数として保持している df_base を使うよりも安全です
    # ----------------------------------------------------
    try:
        # BASE_FILE_PATH はグローバル変数として定義済み
        base_file_df = pd.read_csv(BASE_FILE_PATH)
    except Exception as e:
        # ファイル読み込みエラーが発生した場合のハンドリング
        raise RuntimeError(f"基準ファイルAの再読み込みに失敗しました: {e}")

    # ----------------------------------------------------
    # 2. 変数名の設定 (分かりやすさのため)
    # ----------------------------------------------------
    import_file_df = df_uploaded

    # ----------------------------------------------------
    # 3. 整形ロジックの実行
    # base_file_dfの3行目 (インデックス2) 以降のデータを上書きします
    # ----------------------------------------------------
    try:
        # 列のインデックスは 0 から始まることに注意してください
        # 3列目 (インデックス 3) = '機種' のデータで上書き
        base_file_df.iloc[2:, 3] = import_file_df['機種']
        
        # 4列目 (インデックス 4) = '検定番号' のデータで上書き
        base_file_df.iloc[2:, 4] = import_file_df['検定番号']

    except KeyError as e:
        # インポートしたファイルに必要な列名がない場合のエラーハンドリング
        raise KeyError(f"インポートファイルに必要な列名が見つかりません: {e}。インポートファイルのヘッダーを確認してください。")
    except Exception as e:
        # その他のエラーハンドリング
        raise RuntimeError(f"データの上書き中に予期せぬエラーが発生しました: {e}")

    # 4. 置き換えが完了したDataFrameを返却
    #    この結果がそのままCSVとしてダウンロードされます
    return base_file_df


# DockerのCMDでGunicornを使うため、if __name__ == '__main__': は使用しません。
# ローカルでテストしたい場合は以下をコメントアウト解除して実行できます。
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)