# kakomon.actabit.net（心理院試 過去問索引）

心理学系大学院の入試過去問を検索できる、パスワード制の静的サイトです。
問題データ（`data.bin`）は会員パスワードで暗号化（AES-256-GCM／PBKDF2-SHA256 31万回）してあり、パスワードを知らない人は中身を読めません。
パスワードはこのリポジトリには含まれていません。

## 公開手順（初回のみ）

1. GitHub で新しいリポジトリを作る（例: `kakomon-actabit`）。actabit.net を公開しているのと同じアカウント／組織で作ると、ドメイン確認がそのまま使えます。
   無料プランの GitHub Pages は Public リポジトリが必要です（データは暗号化済みなので Public で問題ありません）。
2. このフォルダの中身（`index.html` `data.bin` `info.json` `CNAME` `robots.txt` `README.md`）をリポジトリ直下にアップロードしてコミット。
3. リポジトリの Settings → Pages → Build and deployment で「Deploy from a branch」、Branch は `main` / `(root)` を選んで Save。
4. 同じ画面の Custom domain に `kakomon.actabit.net` が入っていることを確認（`CNAME` ファイルから自動で入ります）。
5. Google Cloud DNS（actabit.net のゾーン）にレコードを1件追加:
   - 名前: `kakomon`（= kakomon.actabit.net.）
   - タイプ: `CNAME`
   - 値: `<GitHubのユーザー名または組織名>.github.io.`
   - TTL: 300
6. 数分〜1時間ほどで反映されたら、Settings → Pages の「Enforce HTTPS」をオン。

## 月次更新

索引が更新されたら、新しい `data.bin` と `info.json` に差し替えてコミットするだけです（`index.html` はそのまま）。
ソルトを使い回しているので、「ログイン状態を保つ」にしている利用者はパスワードを変えない限り再ログイン不要です。

## パスワードを変えるとき

`build_public.py` で作り直します（Python 3 と `cryptography` が必要）:

    KAKOMON_PASSWORD='新しいパスワード' python3 build_public.py --questions questions.jsonl --record 臨床心理系入試問題_収集記録.json --out .

パスワードを変えると、保存済みのログインはすべて無効になります。
