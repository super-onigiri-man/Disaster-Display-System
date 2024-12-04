import requests
import pandas as pd
import datetime
from datetime import datetime
from cmcrameri import cm # 色
import numpy as np  # アメダスデータの調整
import pydeck as pdk  # 地図の描画
import streamlit as st  # Streamlitをインポート
import statistics  # 座標の中央値を求めるに使用
import sys


# ページ設定
st.set_page_config(page_title="雨量グラフ化", layout="wide", initial_sidebar_state="collapsed",page_icon="☂")

def get_now_date():
    # 気象庁公式から時刻を得る
    url = "https://www.jma.go.jp/bosai/amedas/data/latest_time.txt"
    response = requests.get(url)
    amedas_time = response.text.strip()

    # ISO 8601形式の文字列をdatetimeオブジェクトに変換
    date_object = datetime.fromisoformat(amedas_time)

    # 指定された形式に変換して出力
    amedas_time = date_object.strftime('%Y%m%d%H%M%S')
    # print(amedas_time)

    formatted_time = date_object.strftime('%Y年%m月%d日 %H時%M分')
    # print(str(formatted_time)+'現在')

    return amedas_time,formatted_time

def get_now_snow_time():
    
    # 気象庁公式から時刻を得る
    url = "https://www.jma.go.jp/bosai/amedas/data/latest_time.txt"
    response = requests.get(url)
    amedas_time = response.text.strip()

    # ISO 8601形式の文字列をdatetimeオブジェクトに変換
    date_object = datetime.fromisoformat(amedas_time)

    # 時刻を丸める（分と秒をゼロにする）
    rounded_date_object = date_object.replace(minute=0, second=0)

    # 必要に応じて元の形式での出力も持たせたままにできます
    amedas_time = rounded_date_object.strftime('%Y%m%d%H%M%S')
    formatted_time = rounded_date_object.strftime('%Y年%m月%d日 %H時%M分')
    print(amedas_time)

    return amedas_time, formatted_time

def get_data(amedas_time):

    # アメダスデータ取得
    url = "https://www.jma.go.jp/bosai/amedas/data/map/" + str(amedas_time) + ".json"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame.from_dict(data, orient='index')
    df = df[['precipitation10m', 'precipitation1h', 'precipitation24h']]
    df.columns = ['１０分間雨量', '１時間雨量', '２４時間雨量']
    for col in df.columns:
        df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) else x)

    # 地点情報の取得
    url = "https://www.jma.go.jp/bosai/amedas/const/amedastable.json"
    response = requests.get(url)
    data = response.json()
    df2 = pd.DataFrame.from_dict(data, orient='index')
    df2.drop(columns=['type', 'elems', 'alt', 'enName'], inplace=True) #いらない情報を削除
    df2[['lat1', 'lat2']] = pd.DataFrame(df2['lat'].tolist(), index=df2.index)
    df2[['lon1', 'lon2']] = pd.DataFrame(df2['lon'].tolist(), index=df2.index)
    df2['lat'] = df2['lat1'] + df2['lat2'] / 60 #緯度経度を１０進法に変換
    df2['lon'] = df2['lon1'] + df2['lon2'] / 60 
    df2.drop(columns=['lat1', 'lat2', 'lon1', 'lon2'], inplace=True)

    # アメダス地点とアメダスデータをアメダス番号で紐づけ
    result = pd.concat([df2, df], axis=1)

    return result

def pref_number(result):

    pref_code_num = {
        # 地方区分に関しては内閣府地方区分Aを参照
        # 豪雪地帯の福井・石川・富山・新潟を北陸地方と区分した
        # 札幌管区気象台
        11:"北海道 宗谷地方",
        12:"北海道 上川地方",
        13:"北海道 留萌地方",
        14:"北海道 石狩地方",
        15:"北海道 空知地方",
        16:"北海道 後志地方",
        17:"北海道 オホーツク地方",
        18:"北海道 根室地方",
        19:"北海道 釧路地方",
        20:"北海道 十勝地方",
        21:"北海道 胆振地方",
        22:"北海道 日高地方",
        23:"北海道 渡島地方",
        24:"北海道 檜山地方",
        # 仙台管区気象台（東北地方）
        31:"青森県",
        32:"秋田県",
        33:"岩手県",
        34:"宮城県",
        35:"山形県",
        36:"福島県",
        # 東京管区気象台（関東地方）
        40:"茨城県",
        41:"栃木県",
        42:"群馬県",
        43:"埼玉県",
        44:"東京都",
        45:"千葉県",
        46:"神奈川県",
        # 中部地方
        48:"長野県",
        49:"山梨県",
        50:"静岡県",
        51:"愛知県",
        52:"岐阜県",
        53:"三重県",
        # 北陸地方
        54:"新潟県",
        55:"富山県",
        56:"石川県",
        57:"福井県",
        # 大阪管区気象台
        60:"滋賀県",
        61:"京都府",
        62:"大阪府",
        63:"兵庫県",
        64:"奈良県",
        65:"和歌山県",
        # 中国地方
        66:"岡山県",
        67:"広島県",
        68:"島根県",
        69:"鳥取県",
        81:"山口県",
        # 四国地方
        71:"徳島県",
        72:"香川県",
        73:"愛媛県",
        74:"高知県",
        # 福岡管区気象台（九州地方）
        82:"福岡県",
        83:"大分県",
        84:"長崎県",
        85:"佐賀県",
        86:"熊本県",
        87:"宮崎県",
        88:"鹿児島県",
        # 沖縄管区気象台
        91:"沖縄県 本島地方",
        92:"沖縄県 南大東・北大東島地方",
        93:"沖縄県 宮古島地方",
        94:"沖縄県 石垣島・八重山地方"
    }

    pref_code_yomi_num = {
        # 地方区分に関しては内閣府地方区分Aを参照
        # 豪雪地帯の福井・石川・富山・新潟を北陸地方と区分した
        # 札幌管区気象台（北海道地方）
        11: "ほっかいどう そうやちほう",
        12: "ほっかいどう かみがわちほう",
        13: "ほっかいどう るもいちほう",
        14: "ほっかいどう いしかりちほう",
        15: "ほっかいどう そらちちほう",
        16: "ほっかいどう しりべしちほう",
        17: "ほっかいどう おほーつくちほう",
        18: "ほっかいどう ねむろちほう",
        19: "ほっかいどう くしろちほう",
        20: "ほっかいどう とかちちほう",
        21: "ほっかいどう いぶりちほう",
        22: "ほっかいどう ひだかちほう",
        23: "ほっかいどう おしまちほう",
        24: "ほっかいどう ひやまちほう",
        # 仙台管区気象台（東北地方）
        31: "あおもりけん",
        32: "あきたけん",
        33: "いわてけん",
        34: "みやぎけん",
        35: "やまがたけん",
        36: "ふくしまけん",
        # 東京管区気象台（関東地方）
        40: "いばらきけん",
        41: "とちぎけん",
        42: "ぐんまけん",
        43: "さいたまけん",
        44: "とうきょうと",
        45: "ちばけん",
        46: "かながわけん",
        # 中部地方
        48: "ながのけん",
        49: "やまなしけん",
        50: "しずおかけん",
        51: "あいちけん",
        52: "ぎふけん",
        53: "みえけん",
        # 北陸地方
        54: "にいがたけん",
        55: "とやまけん",
        56: "いしかわけん",
        57: "ふくいけん",
        # 大阪管区気象台（近畿）
        60: "しがけん",
        61: "きょうとふ",
        62: "おおさかふ",
        63: "ひょうごけん",
        64: "ならけん",
        65: "わかやまけん",
        # 中国地方
        66: "おかやまけん",
        67: "ひろしまけん",
        68: "しまねけん",
        69: "とっとりけん",
        81: "やまぐちけん",
        # 四国地方
        71: "とくしまけん",
        72: "かがわけん",
        73: "えひめけん",
        74: "こうちけん",
        # 福岡管区気象台（九州地方）
        82: "ふくおかけん",
        83: "おおいたけん",
        84: "ながさきけん",
        85: "さがけん",
        86: "くまもとけん",
        87: "みやざきけん",
        88: "かごしまけん",
        # 沖縄管区気象台（沖縄県）
        91: "おきなわけん ほんとうちほう",
        92: "おきなわけん みなみだいとう・きただいとうじまちほう",
        93: "おきなわけん みやこじまちほう",
        94: "おきなわけん いしがきじま・やえやまちほう"
    }

    # 都道府県列の追加
    result['都道府県'] = result.index.str[:2].astype(int).map(pref_code_num).fillna('不明')
    result['都道府県よみ'] = result.index.str[:2].astype(int).map(pref_code_yomi_num).fillna('ふめい')

    # print(result)

    return result

        

def get_snow_data(amedas_time):

    # アメダスデータ取得
    url = "https://www.jma.go.jp/bosai/amedas/data/map/" + str(amedas_time) + ".json"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame.from_dict(data, orient='index')
    print(df)
    df = df[['snow1h','snow6h','snow12h','snow24h']]
    df.columns = ['１時間降雪量','６時間降水量','１２時間降雪量','２４時間降雪量']
    for col in df.columns:
        df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) else x)

    # 地点情報の取得
    url = "https://www.jma.go.jp/bosai/amedas/const/amedastable.json"
    response = requests.get(url)
    data = response.json()
    df2 = pd.DataFrame.from_dict(data, orient='index')
    df2.drop(columns=['type', 'elems', 'alt', 'enName'], inplace=True) #いらない情報を削除
    df2[['lat1', 'lat2']] = pd.DataFrame(df2['lat'].tolist(), index=df2.index)
    df2[['lon1', 'lon2']] = pd.DataFrame(df2['lon'].tolist(), index=df2.index)
    df2['lat'] = df2['lat1'] + df2['lat2'] / 60 #緯度経度を１０進法に変換
    df2['lon'] = df2['lon1'] + df2['lon2'] / 60 
    df2.drop(columns=['lat1', 'lat2', 'lon1', 'lon2'], inplace=True)

    # アメダス地点とアメダスデータをアメダス番号で紐づけ
    result = pd.concat([df2, df], axis=1)

    return result

def select_pref(select_pref_list,result):
    # ['北海道', '東北', '関東', '中部', '北陸', '近畿', '中国', '四国', '九州', '沖縄']
    pref_list = ['北海道', '東北', '関東', '中部', '北陸', '近畿', '中国', '四国', '九州', '沖縄']
    notselect = list(set(pref_list) - set(select_pref_list))

    if set(notselect) == set(pref_list):
        print('OK')
        st.text('地方が選択されていません')
        st.stop()

    for i in notselect:

        if i == '北海道':
            result = result[~result.index.str[:2].astype(int).isin(range(11, 25))] 
        
        elif i == '東北':
            result = result[~result.index.str[:2].astype(int).isin(range(30, 37))]

        elif i == '関東':
            result = result[~result.index.str[:2].astype(int).isin(range(40, 47))]

        elif i == '中部':
            result = result[~result.index.str[:2].astype(int).isin(range(48, 54))]

        elif i == '北陸':
            result = result[~result.index.str[:2].astype(int).isin(range(54, 58))]

        elif i == '近畿':
            result = result[~result.index.str[:2].astype(int).isin(range(60, 66))]

        elif i == '中国':
            result = result[~result.index.str[:2].astype(int).isin([66,67,68,69,81])]

        elif i == '四国':
            result = result[~result.index.str[:2].astype(int).isin(range(71, 75))]

        elif i == '九州':
            result = result[~result.index.str[:2].astype(int).isin(range(82, 89))]

        elif i == '沖縄':
            result = result[~result.index.str[:2].astype(int).isin(range(91, 95))]


    return result


def pre10m_color(result):
    # 降水量分布用カラーマップ（10分）

    result = result.dropna(subset=["１０分間雨量"]) #欠損値があった場合はその観測点削除

    colors = cm.hawaii_r(np.linspace(0, 1, 256))
    rgb_colors = (colors[:, :3] * 255).astype(int).tolist()

    # 最小値（0mm）と最大値を設定　これを参考に色付け
    min_height = 0
    max_height = 50
    result["color"] = result["１０分間雨量"].apply(
        lambda h: rgb_colors[int(255 * ((h - min_height) / (max_height - min_height)))]
    )
    
    dftop3 = result.sort_values(by='１０分間雨量', ascending=False).head(3)
    if dftop3['１０分間雨量'].all() == 0:
        return result,None
    else:
        return result,dftop3

def pre1h_color(result):
    result = result.dropna(subset=["１時間雨量"]) #欠損値があった場合はその観測点削

    colors = cm.hawaii_r(np.linspace(0, 1, 256))
    rgb_colors = (colors[:, :3] * 255).astype(int).tolist()

    # 最小値（0mm）と最大値を設定　これを参考に色付け
    min_height = 0
    max_height = 115
    result["color"] = result["１時間雨量"].apply(
        lambda h: rgb_colors[int(255 * ((h - min_height) / (max_height - min_height)))]
    )

    dftop3 = result.sort_values(by='１時間雨量', ascending=False).head(3)
    if dftop3['１時間雨量'].all() == 0:
        return result,None
    else:
        return result,dftop3



def pre24h_color(result):
    result = result.dropna(subset=["２４時間雨量"]) #欠損値があった場合はその観測点削除

    colors = cm.hawaii_r(np.linspace(0, 1, 256))
    rgb_colors = (colors[:, :3] * 255).astype(int).tolist()

    # 最小値（0mm）と最大値を設定　これを参考に色付け
    min_height = 0
    max_height = 200
    result["color"] = result["２４時間雨量"].apply(
        lambda h: rgb_colors[int(255 * ((h - min_height) / (max_height - min_height)))]
    )

    dftop3 = result.sort_values(by='２４時間雨量', ascending=False).head(3)
    if dftop3['２４時間雨量'].all() == 0:
        return result,None
    else:
        return result,dftop3

def snow1h_color(result):
    # 降雪量分布用カラーマップ（1時間）

    result = result.dropna(subset=["１時間降雪量"]) #欠損値があった場合はその観測点削除

    colors = cm.hawaii_r(np.linspace(0, 1, 256))
    rgb_colors = (colors[:, :3] * 255).astype(int).tolist()

    # 最小値（0cm）と最大値を設定　これを参考に色付け
    min_height = 0
    max_height = 25
    result["color"] = result["１時間降雪量"].apply(
        lambda h: rgb_colors[int(255 * ((h - min_height) / (max_height - min_height)))]
    )

    dftop3 = result.sort_values(by='１時間降雪量', ascending=False).head(3)
    if dftop3['１時間降雪量'].all() == 0:
        return result,None
    else:
        return result,dftop3

def snow12h_color(result):
    # 降雪量分布用カラーマップ（12時間）

    result = result.dropna(subset=["１２時間降雪量"]) #欠損値があった場合はその観測点削除

    colors = cm.hawaii_r(np.linspace(0, 1, 256))
    rgb_colors = (colors[:, :3] * 255).astype(int).tolist()

    # 最小値（0cm）と最大値を設定　これを参考に色付け
    min_height = 0
    max_height = 150
    result["color"] = result["１２時間降雪量"].apply(
        lambda h: rgb_colors[int(255 * ((h - min_height) / (max_height - min_height)))]
    )

    dftop3 = result.sort_values(by='１２時間降雪量', ascending=False).head(3)
    if dftop3['１２時間降雪量'].all() == 0:
        return result,None
    else:
        return result,dftop3

def snow24h_color(result):
    # 降雪量分布用カラーマップ（24時間）

    result = result.dropna(subset=["２４時間降雪量"]) #欠損値があった場合はその観測点削除

    colors = cm.hawaii_r(np.linspace(0, 1, 256))
    rgb_colors = (colors[:, :3] * 255).astype(int).tolist()

    # 最小値（0cm）と最大値を設定　これを参考に色付け
    min_height = 0
    max_height = 500
    result["color"] = result["２４時間降雪量"].apply(
        lambda h: rgb_colors[int(255 * ((h - min_height) / (max_height - min_height)))]
    )

    dftop3 = result.sort_values(by='２４時間降雪量', ascending=False).head(3)
    if dftop3['２４時間降雪量'].all() == 0:
        return result,None
    else:
        return result,dftop3


def main():

    st.info('この情報は気象庁からの情報を取得していますが、速報値のため正確性は保証できません', icon=None)

    selected_item = st.multiselect('表示させたい地方を選択してください（デフォルトは全国表示）', ['北海道', '東北', '関東', '中部', '北陸', '近畿', '中国', '四国', '九州', '沖縄'], default=['北海道', '東北', '関東', '中部', '北陸', '近畿', '中国', '四国', '九州', '沖縄'])

    option = st.selectbox(
        '表示させたい内容を選択してください',
        ['10分間降水量', '1時間降水量', '24時間降水量','1時間降雪量','12時間降雪量','24時間降雪量']
    )

    
    if st.button('実行'):
        if option == '10分間降水量':
            data = get_data(get_now_date()[0])
            data = pref_number(data)
            data = select_pref(selected_item,data)
            data = pre10m_color(data)[0]
            st.text(str(get_now_date()[1])+'現在')
            layer = pdk.Layer(
                "ColumnLayer",
                data=data,
                get_position=["lon", "lat"],
                get_elevation='１０分間雨量',
                elevation_scale=2500,
                radius=2500,
                elevation_range=[0, 500],
                get_fill_color='color',
                get_line_color=[0, 0, 0],
                pickable=True,
                auto_highlight=True,
                extruded=True,
            )

            tooltip = {
                "html": "都道府県：<ruby>{都道府県}<rt>{都道府県よみ}</rt></ruby><br>地点名：<ruby>{kjName}<rt>{knName}</rt></ruby><br>10分間雨量：{１０分間雨量}mm",
                "style": {"background": "grey", "color": "white", "font-family": '"ヒラギノ角ゴ Pro W3", "Meiryo", sans-serif', "z-index": "5000"},
            }

            # 視点・ズームレベルの設定
            view_state = pdk.ViewState(
                longitude=statistics.median(data['lon']),
                latitude=statistics.median(data['lat']),
                zoom=4,
                min_zoom=3,
                max_zoom=15,
                pitch=50,
                bearing=-0
            )

            r = pdk.Deck(layer, tooltip=tooltip, initial_view_state=view_state)

            st.pydeck_chart(r)

            if pre10m_color(data)[1] is None:
                st.write('選択された地方では現在、0.5mm以上の降水は観測されていません')
            else:
                rankpre10m = pre10m_color(data)[1][['都道府県','kjName','knName','１０分間雨量']]
                rankpre10m.columns = ['都道府県名','地点名','地点名（よみ）','10分間雨量']
                st.write('10分間降水量ランキング')
                st.write(rankpre10m)

        elif option == '1時間降水量':
            data = get_data(get_now_date()[0])
            data = pref_number(data)
            data = select_pref(selected_item,data)
            data = pre1h_color(data)[0]
            st.text(str(get_now_date()[1])+'現在')
            layer = pdk.Layer(
                "ColumnLayer",
                data=data,
                get_position=["lon", "lat"],
                get_elevation='１時間雨量',
                elevation_scale=2500,
                radius=2500,
                elevation_range=[0, 500],
                get_fill_color='color',
                get_line_color=[0, 0, 0],
                pickable=True,
                auto_highlight=True,
                extruded=True,
            )

            tooltip = {
                "html": "都道府県：<ruby>{都道府県}<rt>{都道府県よみ}</rt></ruby><br>地点名：<ruby>{kjName}<rt>{knName}</rt></ruby><br>1時間雨量：{１時間雨量}mm",
                "style": {"background": "grey", "color": "white", "font-family": '"ヒラギノ角ゴ Pro W3", "Meiryo", sans-serif', "z-index": "5000"},
            }

            view_state = pdk.ViewState(
                longitude=statistics.median(data['lon']),
                latitude=statistics.median(data['lat']),
                zoom=5,
                min_zoom=1,
                max_zoom=15,
                pitch=50,
                bearing=-0
            )

            r = pdk.Deck(layer, tooltip=tooltip, initial_view_state=view_state)

            st.pydeck_chart(r)

            
            if pre1h_color(data)[1] is None:
                st.write('選択された地方では現在、0.5mm以上の降水は観測されていません')
            else:
                rankpre1h = pre1h_color(data)[1][['都道府県','kjName','knName','１時間雨量']]
                rankpre1h.columns = ['都道府県名','地点名','地点名（よみ）','1時間雨量']
                st.write('1時間降水量ランキング')
                st.write(rankpre1h)

        elif option == '24時間降水量':
            data = get_data(get_now_date()[0])
            data = pref_number(data)
            data = select_pref(selected_item,data)
            data = pre24h_color(data)[0]
            st.text(str(get_now_date()[1])+'現在')
            layer = pdk.Layer(
                "ColumnLayer",
                data=data,
                get_position=["lon", "lat"],
                get_elevation='２４時間雨量',
                elevation_scale=2500,
                radius=2500,
                elevation_range=[0, 500],
                get_fill_color='color',
                get_line_color=[0, 0, 0],
                pickable=True,
                auto_highlight=True,
                extruded=True,
            )

            tooltip = {
                "html": "都道府県：<ruby>{都道府県}<rt>{都道府県よみ}</rt></ruby><br>地点名：<ruby>{kjName}<rt>{knName}</rt></ruby><br>24時間雨量：{２４時間雨量}mm",
                "style": {"background": "grey", "color": "white", "font-family": '"ヒラギノ角ゴ Pro W3", "Meiryo", sans-serif', "z-index": "5000"},
            }

            view_state = pdk.ViewState(
                longitude=statistics.median(data['lon']),
                latitude=statistics.median(data['lat']),
                zoom=5,
                min_zoom=1,
                max_zoom=15,
                pitch=50,
                bearing=-0
            )

            r = pdk.Deck(layer, tooltip=tooltip, initial_view_state=view_state)

            st.pydeck_chart(r)

            
            if pre24h_color(data)[1] is None:
                st.write('選択された地方では現在、0.5mm以上の降水は観測されていません')
            else:
                rankpre24h = pre24h_color(data)[1][['都道府県','kjName','knName','２４時間雨量']]
                rankpre24h.columns = ['都道府県名','地点名','地点名（よみ）','24時間雨量']
                st.write('24時間降水量ランキング')
                st.write(rankpre24h)

        elif option == '1時間降雪量':
            data = get_snow_data(get_now_snow_time()[0])
            data = pref_number(data)
            data = select_pref(selected_item,data)
            data = snow1h_color(data)[0]

            st.text(str(get_now_snow_time()[1])+'現在')
            layer = pdk.Layer(
                "ColumnLayer",
                data=data,
                get_position=["lon", "lat"],
                get_elevation='１時間降雪量',
                elevation_scale=2500,
                radius=2500,
                elevation_range=[0, 500],
                get_fill_color='color',
                get_line_color=[0, 0, 0],
                pickable=True,
                auto_highlight=True,
                extruded=True,
            )

            tooltip = {
                "html": "都道府県：<ruby>{都道府県}<rt>{都道府県よみ}</rt></ruby><br>地点名：<ruby>{kjName}<rt>{knName}</rt></ruby><br>1時間降雪量：{１時間降雪量}cm",
                "style": {"background": "grey", "color": "white", "font-family": '"ヒラギノ角ゴ Pro W3", "Meiryo", sans-serif', "z-index": "5000"},
            }

            # 視点・ズームレベルの設定
            view_state = pdk.ViewState(
                longitude=statistics.median(data['lon']),
                latitude=statistics.median(data['lat']),
                zoom=4,
                min_zoom=3,
                max_zoom=15,
                pitch=50,
                bearing=-0
            )

            r = pdk.Deck(layer, tooltip=tooltip, initial_view_state=view_state)

            st.pydeck_chart(r)

            if snow1h_color(data)[1] is None:
                st.write('選択された地方では現在、1cm以上の降雪は観測されていません')
            else:
                ranksnow1h = snow1h_color(data)[1][['都道府県','kjName','knName','１時間降雪量']]
                ranksnow1h.columns = ['都道府県名','地点名','地点名（よみ）','1時間降雪量']
                st.write('1時間降雪量ランキング')
                st.write(ranksnow1h)

        elif option == '12時間降雪量':
            data = get_snow_data(get_now_snow_time()[0])
            data = pref_number(data)
            data = select_pref(selected_item,data)
            data = snow12h_color(data)[0]

            st.text(str(get_now_snow_time()[1])+'現在')
            layer = pdk.Layer(
                "ColumnLayer",
                data=data,
                get_position=["lon", "lat"],
                get_elevation='１２時間降雪量',
                elevation_scale=2500,
                radius=2500,
                elevation_range=[0, 500],
                get_fill_color='color',
                get_line_color=[0, 0, 0],
                pickable=True,
                auto_highlight=True,
                extruded=True,
            )

            tooltip = {
                "html": "都道府県：<ruby>{都道府県}<rt>{都道府県よみ}</rt></ruby><br>地点名：<ruby>{kjName}<rt>{knName}</rt></ruby><br>12時間降雪量：{１２時間降雪量}cm",
                "style": {"background": "grey", "color": "white", "font-family": '"ヒラギノ角ゴ Pro W3", "Meiryo", sans-serif', "z-index": "5000"},
            }

            # 視点・ズームレベルの設定
            view_state = pdk.ViewState(
                longitude=statistics.median(data['lon']),
                latitude=statistics.median(data['lat']),
                zoom=4,
                min_zoom=3,
                max_zoom=15,
                pitch=50,
                bearing=-0
            )

            r = pdk.Deck(layer, tooltip=tooltip, initial_view_state=view_state)

            st.pydeck_chart(r)
            

            if snow12h_color(data)[1] is None:
                st.write('選択された地方では現在、1cm以上の降雪は観測されていません')
            else:
                ranksnow12h = snow12h_color(data)[1][['都道府県','kjName','knName','１２時間降雪量']]
                ranksnow12h.columns = ['都道府県名','地点名','地点名（よみ）','12時間降雪量']
                st.write('12時間降雪量ランキング')
                st.write(ranksnow12h)

        elif option == '24時間降雪量':
            data = get_snow_data(get_now_snow_time()[0])
            data = pref_number(data)
            data = select_pref(selected_item,data)
            data = snow24h_color(data)[0]

            st.text(str(get_now_snow_time()[1])+'現在')
            layer = pdk.Layer(
                "ColumnLayer",
                data=data,
                get_position=["lon", "lat"],
                get_elevation='２４時間降雪量',
                elevation_scale=2500,
                radius=2500,
                elevation_range=[0, 500],
                get_fill_color='color',
                get_line_color=[0, 0, 0],
                pickable=True,
                auto_highlight=True,
                extruded=True,
            )

            tooltip = {
                "html": "都道府県：<ruby>{都道府県}<rt>{都道府県よみ}</rt></ruby><br>地点名：<ruby>{kjName}<rt>{knName}</rt></ruby><br>24時間降雪量：{２４時間降雪量}cm",
                "style": {"background": "grey", "color": "white", "font-family": '"ヒラギノ角ゴ Pro W3", "Meiryo", sans-serif', "z-index": "5000"},
            }

            # 視点・ズームレベルの設定
            view_state = pdk.ViewState(
                longitude=statistics.median(data['lon']),
                latitude=statistics.median(data['lat']),
                zoom=4,
                min_zoom=3,
                max_zoom=15,
                pitch=50,
                bearing=-0
            )

            r = pdk.Deck(layer, tooltip=tooltip, initial_view_state=view_state)

            st.pydeck_chart(r)

            
            if snow24h_color(data)[1] is None:
                st.write('選択された地方では現在、1cm以上の降雪は観測されていません')
            else:
                ranksnow24h = snow24h_color(data)[1][['都道府県','kjName','knName','２４時間降雪量']]
                ranksnow24h.columns = ['都道府県名','地点名','地点名（よみ）','24時間降雪量']
                st.write('24時間降雪量ランキング')
                st.write(ranksnow24h)


if __name__ == "__main__":
    main()