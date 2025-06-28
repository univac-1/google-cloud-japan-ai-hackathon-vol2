from PIL import Image, ImageDraw


def generate_red_square_png(filename="test_image.png", size=(100, 100)):
    """
    指定されたサイズで赤い四角形のPNG画像を生成します。

    Args:
        filename (str): 生成する画像のファイル名。デフォルトは 'test_image.png'。
        size (tuple): 画像の幅と高さ (ピクセル)。デフォルトは (100, 100)。
    """
    try:
        # 新しいRGBA画像を作成 (RGBA: Red, Green, Blue, Alpha)
        # 背景は透明 (Alpha=0)
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 全体を赤色で塗りつぶす (R=255, G=0, B=0, A=255)
        # 赤い四角形を描画
        draw.rectangle([0, 0, size[0], size[1]], fill=(255, 0, 0, 255))

        # 画像をPNG形式で保存
        img.save(filename, "PNG")
        print(f"'{filename}' を生成しました。サイズ: {size[0]}x{size[1]}ピクセル。")
    except ImportError:
        print("エラー: Pillow (PIL) ライブラリがインストールされていません。")
        print("画像を生成するには 'pip install Pillow' を実行してください。")
    except Exception as e:
        print(f"画像の生成中にエラーが発生しました: {e}")


if __name__ == "__main__":
    generate_red_square_png()
