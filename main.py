import codecs
import csv
import io
import mojimoji
import re
import requests
import zipfile

def download():

    # 郵便番号データ（ローマ字）のダウンロード
    response = requests.get("https://www.post.japanpost.jp/zipcode/dl/roman/ken_all_rome.zip?190712")
    if response.status_code != 200:
        e = Exception(f"HTTP status : {response.status_code}")
        raise e

    # ダウンロードデータのファイル出力
    with open("ken_all_rome.zip", "wb") as file:
        file.write(response.content)
    
    # zipファイルの解凍
    with zipfile.ZipFile("./ken_all_rome.zip") as zip:
        zip.extractall("./")

    rome_dic = {}
    rome_file_path = "./KEN_ALL_ROME.CSV"
    with codecs.open(rome_file_path, "r", encoding="shift-jis") as rome:
        reader = csv.reader(rome)

        for row in reader:
            zip_code = row[0]
            prefecture_name = row[1]
            city_name = row[2].replace("　", "")
            town_name = re.sub(r'^(.*?)(（.*)?$', r'\1', row[3]).replace("　", "").replace("以下に掲載がない場合", "")
            prefecture_rome_name = row[4]
            city_rome_name = row[5].replace(" ", "-").lower()
            town_rome_name = re.sub(r'^(.*?)(\(.*)?$', r'\1', row[6]).replace(" ", "").replace("IKANIKEISAIGANAIBAAI", "").lower()

            rome_dic[f"{prefecture_name},{city_name},,"] = { "prefecture_name": prefecture_rome_name, "city_name": city_rome_name, "town_name": "" }
            rome_dic[f"{prefecture_name},{city_name},{town_name},"] = { "prefecture_name": prefecture_rome_name, "city_name": city_rome_name, "town_name": town_rome_name }



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

    kana_dic = {}
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
        city_rome_name = ""
        town_rome_name = ""
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
            if zip_code.replace("-", "") == row[2] and ("（" in town_name) and (not town_name.endswith("）")):
                same_zip_code = True
            else:
                same_zip_code = False

            if not same_zip_code and zip_code:

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

                key = f"{prefecture_name},{city_name},{town_short_name},"
                if key in rome_dic:
                    city_rome_name = rome_dic[key]["city_name"]
                    town_rome_name = rome_dic[key]["town_name"]
                else:
                    city_rome_name = ""
                    town_rome_name = ""

                kana_dic[f"{prefecture_name},{city_name},,"] = { "city_name": city_kana_name, "town_name": "" }
                kana_dic[f"{prefecture_name},{city_name},{town_short_name},"] = { "city_name": city_kana_name, "town_name": town_short_kana_name }
                dest.write(f"{zip_code},{zip_code_branch_no[zip_code]},{area_code},{prefecture_name},{city_name},{city_kana_name},{city_rome_name},{town_short_name},{town_short_kana_name},{town_rome_name},{town_ext_name},{town_ext_kana_name},{town_duplicate_flag},{building_flag}\n")

            area_code = row[0] # 全国地方公共団体コード
            # xxx = row[1] # 旧郵便番号5桁
            zip_code = re.sub(r'([0-9]{3})([0-9]{4})', r'\1-\2', row[2]) # 郵便番号
            # xxx = row[3] # 都道府県名（半角カタカナ）
            city_kana_name = mojimoji.han_to_zen(row[4]) # 市区町村名（半角カタカナ）
            town_kana_name = row[5] if not same_zip_code else f"{town_kana_name}{row[5]}" # 町域名（半角カタカナ）
            town_kana_name = mojimoji.han_to_zen(town_kana_name)
            prefecture_name = row[6] # 都道府県名
            city_name = row[7] # 市区町村名
            town_name = row[8] if not same_zip_code else f"{town_name}{row[8]}" # 町域
            town_name = town_name.replace("−", "-").replace("〜", "～")
            town_duplicate_flag = row[9] # 一町域が二以上の郵便番号で表される場合の表示　（注3）　（「1」は該当、「0」は該当せず）
            # xxx = row[10] # 小字毎に番地が起番されている町域の表示　（注4）　（「1」は該当、「0」は該当せず）
            # xxx = row[11] # 丁目を有する町域の場合の表示　（「1」は該当、「0」は該当せず）
            town_multi_flag = row[12] # 一つの郵便番号で二以上の町域を表す場合の表示　（注5）　（「1」は該当、「0」は該当せず）
            # xxx = row[13] # 更新の表示（注6）（「0」は変更なし、「1」は変更あり、「2」廃止（廃止データのみ使用））
            # xxx = row[14] # 変更理由　（「0」は変更なし、「1」市政・区政・町政・分区・政令指定都市施行、「2」住居表示の実施、「3」区画整理、「4」郵便区調整等、「5」訂正、「6」廃止（廃止データのみ使用））


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

        key = f"{prefecture_name},{city_name},{town_short_name},"
        if key in rome_dic:
            city_rome_name = rome_dic[key]["city_name"]
            town_rome_name = rome_dic[key]["town_name"]
        else:
            city_rome_name = ""
            town_rome_name = ""

        kana_dic[f"{prefecture_name},{city_name},,"] = { "city_name": city_kana_name, "town_name": "" }
        kana_dic[f"{prefecture_name},{city_name},{town_short_name},"] = { "city_name": city_kana_name, "town_name": town_short_kana_name }
        dest.write(f"{zip_code},{zip_code_branch_no[zip_code]},{area_code},{prefecture_name},{city_name},{city_kana_name},{city_rome_name},{town_short_name},{town_short_kana_name},{town_rome_name},{town_ext_name},{town_ext_kana_name},{town_duplicate_flag},{building_flag}\n")


    # 郵便番号データ（大口事業所）のダウンロード
    response = requests.get("https://www.post.japanpost.jp/zipcode/dl/jigyosyo/zip/jigyosyo.zip")
    if response.status_code != 200:
        e = Exception(f"HTTP status : {response.status_code}")
        raise e
    
    # ダウンロードデータのファイル出力
    with open("jigyosyo.zip", "wb") as file:
        file.write(response.content)

    # zipファイルの解凍
    with zipfile.ZipFile("./jigyosyo.zip") as zip:
        zip.extractall("./")

    # 文字コード変換(shift-jis -> utf-8)
    src_file_path = "./JIGYOSYO.CSV"
    dest_file_path = "./JIGYOSYO_UTF8.CSV"

    with codecs.open(src_file_path, "r", encoding="cp932") as src, codecs.open(dest_file_path, "w", encoding="utf-8") as dest:
        reader = csv.reader(src)
        area_code = ""
        office_name = ""
        office_kana_name = ""
        zip_code = ""
        prefecture_name = ""
        city_name = ""
        city_kana_name = ""
        city_rome_name = ""
        town_name = ""
        town_kana_name = ""
        town_ext_name = ""
        town_rome_name = ""
        office_flag = 0
        post_office_box_flag = 0
        zip_code_branch_no = {}
        rows = []


        for row in reader:

            area_code = row[0] # 全国地方公共団体コード
            office_kana_name = mojimoji.han_to_zen(row[1]) # 大口事業所名（カナ）
            office_name = row[2] # 大口事業所名（漢字）
            prefecture_name = row[3] # 都道府県名
            city_name = row[4] # 市区町村名
            town_name = row[5] # 町域名
            town_ext_name = row[6] # 小字名、丁目、番地等
            zip_code = re.sub(r'([0-9]{3})([0-9]{4})', r'\1-\2', row[7]) # 郵便番号
            # xxx = row[8] # 旧郵便番号5桁
            # xxx = row[9] # 取扱局
            office_flag = 1 if row[10] == "0" else 0 # 「0」大口事業所、「1」私書箱
            post_office_box_flag = 1 if row[10] == "1" else 0 # 「0」大口事業所、「1」私書箱
            # xxx = row[11] # 複数番号の有無
            # xxx = row[12] # 修正コード

            #city_kana_name = row[4] # 市区町村名（半角カタカナ）
            #town_kana_name = row[5] if not same_zip_code else f"{town_kana_name}{row[5]}" # 町域名（半角カタカナ）

            if zip_code in zip_code_branch_no:
                zip_code_branch_no[zip_code] += 1
            else:
                zip_code_branch_no[zip_code] = 1

            key = f"{prefecture_name},{city_name},{town_name},"
            if key in rome_dic:
                city_rome_name = rome_dic[key]["city_name"]
                town_rome_name = rome_dic[key]["town_name"]
            else:
                town_name_exclude_aza = re.sub(r"(大)?字", "", town_name)
                key = f"{prefecture_name},{city_name},{town_name_exclude_aza},"
                if town_name != town_name_exclude_aza and key in rome_dic:
                    city_rome_name = rome_dic[key]["city_name"]
                    town_rome_name = rome_dic[key]["town_name"]
                else:
                    key = f"{prefecture_name},{city_name},,"
                    if key in rome_dic:
                        city_rome_name = rome_dic[key]["city_name"]
                        town_rome_name = rome_dic[key]["town_name"]
                    else:
                        city_rome_name = ""
                        town_rome_name = ""

            key = f"{prefecture_name},{city_name},{town_name},"
            if key in kana_dic:
                city_kana_name = kana_dic[key]["city_name"]
                town_kana_name = kana_dic[key]["town_name"]
            else:
                town_name_exclude_aza = re.sub(r"(大)?字", "", town_name)
                key = f"{prefecture_name},{city_name},{town_name_exclude_aza},"
                if town_name != town_name_exclude_aza and key in kana_dic:
                    city_kana_name = kana_dic[key]["city_name"]
                    town_kana_name = kana_dic[key]["town_name"]
                else:
                    key = f"{prefecture_name},{city_name},,"
                    if key in kana_dic:
                        city_kana_name = kana_dic[key]["city_name"]
                        town_kana_name = kana_dic[key]["town_name"]
                    else:
                        city_kana_name = ""
                        town_kana_name = ""

            dest.write(f"{zip_code},{zip_code_branch_no[zip_code]},{area_code},{prefecture_name},{city_name},{city_kana_name},{city_rome_name},{town_name},{town_kana_name},{town_rome_name},{town_ext_name},{office_name},{office_kana_name},{office_flag},{post_office_box_flag}\n")

if __name__ == "__main__":
    download()