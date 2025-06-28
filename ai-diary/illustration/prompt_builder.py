def build_prompt(diary_text: str, gender: str) -> str:
    """
    高齢者の性別と絵日記本文から、Vertex AI Imagen 向けのプロンプトを生成する。
    """

    # 性別から人物描写を決定
    if gender == "male":
        person_description = "高齢の男性"
    elif gender == "female":
        person_description = "高齢の女性"
    else:
        person_description = "高齢者"

    # 最終プロンプトを組み立てる
    prompt = (
        f"{person_description}が体験した心温まる場面のイラスト。\n\n"
        f"場面の内容: {diary_text.strip()}\n\n"
        f"柔らかい光と穏やかな雰囲気を含めて、絵本のようなタッチで描写してください。"
    )

    return prompt
