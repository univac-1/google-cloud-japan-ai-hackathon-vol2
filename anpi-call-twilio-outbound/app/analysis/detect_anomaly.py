"""高齢者の異常兆候を検出するクラス"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from openai import OpenAI
from google.cloud import storage
from google.cloud.exceptions import NotFound
from pydantic import BaseModel

from models.transcription import TranscriptionData

logger = logging.getLogger(__name__)


class OpenAIAnalysisResult(BaseModel):
    """OpenAI分析結果（レスポンス型定義用）"""
    has_anomaly: bool
    reason: str
    confidence: float  # 0.0-1.0の信頼度
    detected_issues: List[str]  # 検出された具体的な問題


class AnomalyResult(BaseModel):
    """異常検出結果"""
    has_anomaly: bool
    reason: str
    confidence: float  # 0.0-1.0の信頼度
    detected_issues: List[str]  # 検出された具体的な問題
    source_files: List[str]  # 分析に使用したファイルパス


class AnomalyDetector:
    """高齢者の通話内容から異常兆候を検出するクラス"""
    
    def __init__(self, bucket_name: Optional[str] = None, max_files: int = 5):
        """
        Args:
            bucket_name: GCSバケット名（環境変数GCS_BUCKET_NAMEからも取得可能）
            max_files: 分析する最大ファイル数（デフォルト: 5件）
        """
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME", "univac-aiagent-transcription")
        self.max_files = max_files
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)
        self.openai_client = OpenAI()
        self.files_prefix = "transcriptions/"
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def detect_anomaly(self, user_id: str) -> AnomalyResult:
        """
        指定ユーザーの通話内容から異常兆候を検出
        
        Args:
            user_id: 分析対象のユーザーID
            
        Returns:
            AnomalyResult: 異常検出結果
        """
        try:
            # 直近のファイルを取得
            transcription_files = await self._get_recent_transcription_files(user_id)
            
            if not transcription_files:
                return AnomalyResult(
                    has_anomaly=False,
                    reason="分析対象の通話データが見つかりませんでした",
                    confidence=0.0,
                    detected_issues=[],
                    source_files=[]
                )
            
            # ファイル内容を読み込み
            transcription_data_list = []
            source_files = []
            
            for file_info in transcription_files:
                content = await self._download_file_content(file_info['name'])
                if content:
                    transcription_data_list.append(content)
                    source_files.append(f"gs://{self.bucket_name}/{file_info['name']}")
            
            if not transcription_data_list:
                return AnomalyResult(
                    has_anomaly=False,
                    reason="通話データの読み込みに失敗しました",
                    confidence=0.0,
                    detected_issues=[],
                    source_files=[]
                )
            
            # OpenAI GPT-4o-miniで分析
            analysis_result = await self._analyze_with_openai(transcription_data_list)
            
            # 結果を構造化
            result = AnomalyResult(
                has_anomaly=analysis_result.get("has_anomaly", False),
                reason=analysis_result.get("reason", ""),
                confidence=analysis_result.get("confidence", 0.0),
                detected_issues=analysis_result.get("detected_issues", []),
                source_files=source_files
            )
            
            self.logger.info(f"異常検出完了 user_id: {user_id}, 異常フラグ: {result.has_anomaly}, ソースファイル: {len(source_files)}件")
            
            return result
            
        except Exception as e:
            self.logger.error(f"異常検出エラー user_id: {user_id}, error: {e}", exc_info=True)
            return AnomalyResult(
                has_anomaly=False,
                reason=f"分析中にエラーが発生しました: {str(e)}",
                confidence=0.0,
                detected_issues=[],
                source_files=[]
            )

    async def _get_recent_transcription_files(self, user_id: str) -> List[Dict[str, Any]]:
        """指定ユーザーの直近の文字起こしファイルを取得"""
        try:
            prefix = f"{self.files_prefix}{user_id}/"
            blobs = list(self.bucket.list_blobs(prefix=prefix))
            
            # ファイル名でソート（新しい順）
            file_infos = []
            for blob in blobs:
                if blob.name.endswith('.json'):
                    file_infos.append({
                        'name': blob.name,
                        'updated': blob.updated,
                        'size': blob.size
                    })
            
            # 更新日時でソート（新しい順）
            file_infos.sort(key=lambda x: x['updated'], reverse=True)
            
            # 最大件数まで取得
            recent_files = file_infos[:self.max_files]
            
            self.logger.info(f"user_id: {user_id} の直近ファイル {len(recent_files)}件を取得")
            
            return recent_files
            
        except Exception as e:
            self.logger.error(f"ファイル一覧取得エラー user_id: {user_id}, error: {e}")
            return []

    async def _download_file_content(self, blob_name: str) -> Optional[TranscriptionData]:
        """GCSからファイル内容をダウンロードして解析"""
        try:
            blob = self.bucket.blob(blob_name)
            content = blob.download_as_text(encoding='utf-8')
            
            # JSONをパース
            data = json.loads(content)
            
            # Pydanticモデルに変換
            transcription_data = TranscriptionData.model_validate(data)
            
            return transcription_data
            
        except Exception as e:
            self.logger.error(f"ファイル読み込みエラー blob: {blob_name}, error: {e}")
            return None

    async def _analyze_with_openai(self, transcription_data_list: List[TranscriptionData]) -> Dict[str, Any]:
        """OpenAI GPT-4o-miniで通話内容を分析"""
        try:
            # 分析用のプロンプトを作成
            analysis_prompt = self._create_analysis_prompt(transcription_data_list)
            
            response = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """あなたは高齢者ケアの専門家です。通話記録から高齢者の健康状態や生活状況の異常を検出してください。

以下の観点で分析してください：
1. 健康状態の変化（体調不良、痛み、めまい、転倒など）
2. 認知機能の変化（記憶の混乱、判断力の低下、会話の一貫性など）
3. 生活状況の変化（食事の変化、睡眠の問題、孤立感など）
4. 感情状態の変化（うつ状態、不安、怒りやすさなど）
5. 緊急性のある状況（転倒、怪我、病気の症状など）"""
                    },
                    {
                        "role": "user", 
                        "content": analysis_prompt
                    }
                ],
                response_format=OpenAIAnalysisResult,
                temperature=0.1,  # 一貫性を重視
                max_tokens=1000
            )
            
            # 構造化されたレスポンスを取得
            parsed_result = response.choices[0].message.parsed
            
            if parsed_result:
                return parsed_result.model_dump()
            else:
                # パースに失敗した場合のフォールバック
                self.logger.warning("OpenAIレスポンスの構造化パースに失敗")
                return {
                    "has_anomaly": False,
                    "reason": "分析結果の解析に失敗しました",
                    "confidence": 0.0,
                    "detected_issues": []
                }
                
        except Exception as e:
            self.logger.error(f"OpenAI分析エラー: {e}")
            return {
                "has_anomaly": False,
                "reason": f"AI分析中にエラーが発生しました: {str(e)}",
                "confidence": 0.0,
                "detected_issues": []
            }

    def _create_analysis_prompt(self, transcription_data_list: List[TranscriptionData]) -> str:
        """分析用のプロンプトを作成"""
        # 通話開始日時でグループ化
        calls_by_datetime = {}
        for data in transcription_data_list:
            call_datetime = data.call_started_at.strftime("%Y年%m月%d日 %H:%M")
            if call_datetime not in calls_by_datetime:
                calls_by_datetime[call_datetime] = []
            calls_by_datetime[call_datetime].append(data)
        
        # 日時順でソート（古い順）
        sorted_calls = sorted(calls_by_datetime.items(), key=lambda x: x[0])
        
        prompt_parts = ["以下は高齢者との通話記録です。時系列順に並んでいます。異常な兆候がないか分析してください。\n"]
        
        for call_datetime, data_list in sorted_calls:
            prompt_parts.append(f"=== 通話: {call_datetime} ===")
            
            if len(data_list) == 1:
                # 単一ファイルの場合
                prompt_parts.append(data_list[0].formatted_text)
            else:
                # 複数ファイルの場合は連続した会話として結合
                # 保存回数順でソート（ファイル名の末尾の数字で判断）
                sorted_data = sorted(data_list, key=lambda x: x.saved_at)
                
                prompt_parts.append("（この通話は複数回に分けて記録されています）")
                
                all_transcriptions = []
                for data in sorted_data:
                    all_transcriptions.extend(data.transcriptions)
                
                # 時系列順でソート
                all_transcriptions.sort(key=lambda x: x.timestamp)
                
                # 連続した会話として整形
                for transcription in all_transcriptions:
                    speaker = "ユーザー" if transcription.speaker == "user" else "エージェント"
                    prompt_parts.append(f"{speaker}: {transcription.text}")
            
            prompt_parts.append("")  # 通話間の区切り
        
        prompt_parts.append("上記の通話記録を時系列で分析して、高齢者の異常兆候を検出してください。")
        
        return "\n".join(prompt_parts)