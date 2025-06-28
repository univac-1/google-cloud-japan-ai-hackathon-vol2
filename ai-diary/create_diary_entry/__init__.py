"""
日記生成パッケージ

ユーザー情報と会話履歴から日記風の文章を生成する機能を提供
"""

from .gemini_service import DiaryGenerator

__all__ = ['DiaryGenerator'] 