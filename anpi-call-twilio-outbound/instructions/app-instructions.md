# アプリケーションの開発ルール
## コーディング規約

### レイヤを分離する
websocket周りの処理はControllerとしてmain.pyに書き、それ以外の処理はmodelレイヤーに分けること

### Pydanticをつかって型付けする
privateメソッドは必ず、_というprefixをメソッド名につけること

### 機密情報をべた書きしない

githubにpublic repositoryでアップロードしても問題ないような構成にする

ローカル実行時は、.envを使用し、.envはgit管理外とする

## エージェントの実装の仕方
基本的にopenaiを利用するものとする。

特に通話エージェントは、必ずopenai-realtimeapiで実装すること。
realtimeapiのサンプルは、code-samples/ディレクトリを参考にすること。

発話の終了検出にはopenaiのvadを利用するものとし、勝手に発話の終了を判断してcommitなどは絶対に行わないこと
