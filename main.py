import codecs
import csv
import io
import mojimoji
import re
import requests
import zipfile

def download():

    # 郵便番号データのダウンロード
    response = requests.get("https://www.post.japanpost.jp/zipcode/dl/kogaki/zip/ken_all.zip")
    if response.status_code != 200:
        e = Exception(f"HTTP status : {response.status_code}")
        raise e
    
    # ダウンロードデータのファイル出力
    with open("ken_all.zip", "wb") as file:
        file.write(response.content)

    # zipファイルの解凍
    with zipfile.ZipFile("./ken_all.zip") as zip:
        zip.extractall("./")

    # 文字コード変換(shift-jis -> utf-8)
    src_file_path = "./KEN_ALL.CSV"
    dest_file_path = "./KEN_ALL_UTF8.CSV"

    with codecs.open(src_file_path, "r", encoding="shift-jis") as src, codecs.open(dest_file_path, "w", encoding="utf-8") as dest:
        reader = csv.reader(src)
        area_code = ""
        zip_code = ""
        city_kana_name = ""
        town_kana_name = ""
        prefecture_name = ""
        city_name = ""
        town_name = ""
        town_short_name = ""
        town_ext_name = ""
        town_duplicate_flag = ""
        town_multi_flag = ""
        zip_code_branch_no = {}
        same_zip_code = False
        rows = []
        building_flag = 0
        exclude_building = False
        building_prefix = ""
        building_kana_prefix = ""


        for row in reader:
            if zip_code == row[2] and ("（" in town_name) and not re.match(r".*）$", town_name):
                same_zip_code = True
            else:
                same_zip_code = False

            if not same_zip_code and zip_code:
                town_name.replace("−", "-").replace("〜", "～")
                town_kana_name = mojimoji.han_to_zen(town_kana_name)

                if town_name == "以下に掲載がない場合":
                    town_short_name = ""
                    town_ext_name = town_name
                    town_short_kana_name = ""
                    town_ext_kana_name = town_kana_name
                else:
                    town_short_name = re.sub(r"（.*）", "", town_name)
                    town_ext_name = town_name.replace(town_short_name, "", 1)
                    town_short_kana_name = re.sub(r"（.*）", "", town_kana_name)
                    town_ext_kana_name = town_kana_name.replace(town_short_kana_name, "", 1)
                
                if town_ext_name ==  "（次のビルを除く）":
                    exclude_building = True
                    building_flag = 0
                    town_duplicate_flag = 1
                    building_prefix = town_short_name
                    building_kana_prefix = town_short_kana_name
                elif exclude_building and town_short_name.startswith(building_prefix):
                    building_flag = 1
                    town_duplicate_flag = 1
                    town_ext_name = f"{town_short_name}{town_ext_name}".replace(building_prefix, "", 1)
                    town_short_name = building_prefix
                    town_ext_kana_name = f"{town_short_kana_name}{town_ext_kana_name}".replace(building_kana_prefix, "", 1)
                    town_short_kana_name = building_kana_prefix
                else:
                    building_flag = 0
                    exclude_building = False

                if zip_code in zip_code_branch_no:
                    zip_code_branch_no[zip_code] += 1
                else:
                    zip_code_branch_no[zip_code] = 1

                dest.write(f"{zip_code},{zip_code_branch_no[zip_code]},{area_code},{prefecture_name},{city_name},{town_short_name},{town_ext_name},{mojimoji.han_to_zen(city_kana_name)},{town_short_kana_name},{town_ext_kana_name},{town_duplicate_flag},{town_multi_flag},{building_flag}\n")

            area_code = row[0] # 全国地方公共団体コード
            # xxx = row[1] # 旧郵便番号5桁
            zip_code = re.sub(r'([0-9]{3})([0-9]{4})', r'\1-\2', row[2]) # 郵便番号
            # xxx = row[3] # 都道府県名（半角カタカナ）
            city_kana_name = row[4] # 市区町村名（半角カタカナ）
            town_kana_name = row[5] if not same_zip_code else f"{town_kana_name}{row[5]}" # 町域名（半角カタカナ）
            prefecture_name = row[6] # 都道府県名
            city_name = row[7] # 市区町村名
            town_name = row[8] if not same_zip_code else f"{town_name}{row[8]}" # 町域
            town_duplicate_flag = row[9] # 一町域が二以上の郵便番号で表される場合の表示　（注3）　（「1」は該当、「0」は該当せず）
            # xxx = row[10] # 小字毎に番地が起番されている町域の表示　（注4）　（「1」は該当、「0」は該当せず）
            # xxx = row[11] # 丁目を有する町域の場合の表示　（「1」は該当、「0」は該当せず）
            town_multi_flag = row[12] # 一つの郵便番号で二以上の町域を表す場合の表示　（注5）　（「1」は該当、「0」は該当せず）
            # xxx = row[13] # 更新の表示（注6）（「0」は変更なし、「1」は変更あり、「2」廃止（廃止データのみ使用））
            # xxx = row[14] # 変更理由　（「0」は変更なし、「1」市政・区政・町政・分区・政令指定都市施行、「2」住居表示の実施、「3」区画整理、「4」郵便区調整等、「5」訂正、「6」廃止（廃止データのみ使用））


        town_kana_name = mojimoji.han_to_zen(town_kana_name)

        town_short_name = re.sub(r"（.*）", "", town_name)
        town_ext_name = town_name.replace(town_short_name, "", 1)
        town_short_kana_name = re.sub(r"（.*）", "", town_kana_name)
        town_ext_kana_name = town_kana_name.replace(town_short_kana_name, "", 1)

        if exclude_building and town_short_name.startswith(building_prefix):
            building_flag = 1
            town_duplicate_flag = 1
            town_ext_name = f"{town_short_name}{town_ext_name}".replace(building_prefix, "", 1)
            town_short_name = building_prefix
            town_ext_kana_name = f"{town_short_kana_name}{town_ext_kana_name}".replace(building_kana_prefix, "", 1)
            town_short_kana_name = building_kana_prefix
        else:
            building_flag = 0
            exclude_building = False

        if zip_code in zip_code_branch_no:
            zip_code_branch_no[zip_code] += 1
        else:
            zip_code_branch_no[zip_code] = 1

        dest.write(f"{zip_code},{zip_code_branch_no[zip_code]},{area_code},{prefecture_name},{city_name},{town_short_name},{town_ext_name},{mojimoji.han_to_zen(city_kana_name)},{town_short_kana_name},{town_ext_kana_name},{town_duplicate_flag},{town_multi_flag},{building_flag}\n")


if __name__ == "__main__":
    download()