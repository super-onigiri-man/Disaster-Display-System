import requests
import pandas as pd
import datetime
from datetime import timedelta, timezone,datetime
from cmcrameri import cm #色
import numpy as np #アメダスデータの調整
import pydeck as pdk #地図の描画
import streamlit as st  # Streamlitをインポート
import statistics #座標の中央値を求めるに使用

# ストリームリット用ページ設定をスクリプトの最初に配置
st.set_page_config(page_title="10分間雨量", layout="wide", initial_sidebar_state="collapsed")

def get_data():
    # 気象庁公式から時刻を得る
    url = "https://www.jma.go.jp/bosai/amedas/data/latest_time.txt"
    response = requests.get(url)
    amedas_time = response.text.strip()

    # ISO 8601形式の文字列をdatetimeオブジェクトに変換
    date_object = datetime.fromisoformat(amedas_time)

    # 指定された形式に変換して出力
    amedas_time = date_object.strftime('%Y%m%d%H%M%S')
    # print(amedas_time)

    # formatted_time = date_object.strftime('%Y年%m月%d日 %H時%M分')
    # print(str(formatted_time)+'現在')


    url = "https://www.jma.go.jp/bosai/amedas/data/map/" + str(amedas_time) + ".json"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame.from_dict(data, orient='index')
    df = df[['temp', 'humidity', 'precipitation10m', 'precipitation1h', 'precipitation24h', 'windDirection', 'wind']]
    df.columns = ['気温', '湿度', '１０分間雨量', '１時間雨量', '２４時間雨量', '風向', '風速']
    for col in df.columns:
        df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) else x)

    url = "https://www.jma.go.jp/bosai/amedas/const/amedastable.json"
    response = requests.get(url)
    data = response.json()
    df2 = pd.DataFrame.from_dict(data, orient='index')
    df2.drop(columns=['type', 'elems', 'alt', 'enName'], inplace=True)
    df2[['lat1', 'lat2']] = pd.DataFrame(df2['lat'].tolist(), index=df2.index)
    df2[['lon1', 'lon2']] = pd.DataFrame(df2['lon'].tolist(), index=df2.index)
    df2['lat'] = df2['lat1'] + df2['lat2'] / 60
    df2['lon'] = df2['lon1'] + df2['lon2'] / 60
    df2.drop(columns=['lat1', 'lat2', 'lon1', 'lon2'], inplace=True)

    result = pd.concat([df2, df], axis=1)

    return result

def temp_color(result):
    result = result.dropna(subset=["気温"]) #欠損値があった場合はその観測点削除

    colors = cm.hawaii_r(np.linspace(0, 1, 256))
    rgb_colors = (colors[:, :3] * 255).astype(int).tolist()

    # Now the min and max functions should work correctly
    min_height = -5
    max_height = 35
    result["color"] = result["気温"].apply(
        lambda h: rgb_colors[int(255 * ((h - min_height) / (max_height - min_height)))]
    )

    return result

def pre10m_color(result):
    result = result.dropna(subset=["１０分間雨量"]) #欠損値があった場合はその観測点削除

    colors = cm.hawaii_r(np.linspace(0, 1, 256))
    rgb_colors = (colors[:, :3] * 255).astype(int).tolist()

    # Now the min and max functions should work correctly
    min_height = 0
    max_height = 50
    result["color"] = result["１０分間雨量"].apply(
        lambda h: rgb_colors[int(255 * ((h - min_height) / (max_height - min_height)))]
    )

    return result

def pre1h_color(result):

    result = result.dropna(subset=["１時間雨量"]) #欠損値があった場合はその観測点削

    colors = cm.hawaii_r(np.linspace(0, 1, 256))
    rgb_colors = (colors[:, :3] * 255).astype(int).tolist()

    # Now the min and max functions should work correctly
    min_height = 0
    max_height = result["１時間雨量"].max()
    result["color"] = result["１時間雨量"].apply(
        lambda h: rgb_colors[int(255 * ((h - min_height) / (max_height - min_height)))]
    )

    return result

def pre24h_color(result):
    result = result.dropna(subset=["２４時間雨量"])

    colors = cm.hawaii_r(np.linspace(0, 1, 256))
    rgb_colors = (colors[:, :3] * 255).astype(int).tolist()

    min_height = 0
    max_height = 200
    result["color"] = result["２４時間雨量"].apply(
        lambda h: rgb_colors[int(255 * ((h - min_height) / (max_height - min_height)))]
    )

    return result

def main():

    option = st.selectbox(
    '表示させたい内容を選択してください', 
    ['10分間降水量', '1時間降水量', '24時間降水量' , '気温']
    )

    if st.button('実行'):
        if option == '10分間降水量':
            data = get_data()
            data = pre10m_color(data)
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
                "html": "地点名：<ruby>{kjName}<rt>{knName}</rt></ruby><br>10分間雨量：{１０分間雨量}mm",
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

   

    if option == '1時間降水量':
            data = get_data()
            data = pre1h_color(data)
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
                "html": "地点名：<ruby>{kjName}<rt>{knName}</rt></ruby><br>1時間雨量：{１時間雨量}mm",
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


    if option == '24時間降水量':
            data = get_data()
            data = pre24h_color(data)
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
                "html": "地点名：<ruby>{kjName}<rt>{knName}</rt></ruby><br>24時間雨量：{２４時間雨量}mm",
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

    if option == '気温':
            data = get_data()
            data = temp_color(data)
            layer = pdk.Layer(
                "ColumnLayer",
                data=data,
                get_position=["lon", "lat"],
                get_elevation='気温',
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
                "html": "地点名：<ruby>{kjName}<rt>{knName}</rt></ruby><br>気温：{気温}℃",
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


if __name__ == "__main__":
    main()