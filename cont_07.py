import plotly.graph_objects as go
import numpy as np
from control.matlab import *
import streamlit as st

# streamlitの表示用リストとタブ
options = ['1次遅れ系','1次遅れ+積分要素','2次遅れ系','任意']
option = st.sidebar.selectbox('モデル設定', options)

ulist = ['ステップ','正弦波']
ut = st.sidebar.selectbox('入力設定', ulist)

K = st.sidebar.slider('K:ゲイン', -1.00, 2.00, 1.00)
T = st.sidebar.slider('T:時定数', -1.00, 2.00, 1.00)
Z = st.sidebar.slider('ζ:減衰係数', -1.00, 2.00, 1.00)
W = st.sidebar.slider('Wn:固有角周波数', -10.00, 10.00, 1.00)
st.sidebar.divider()
fz = st.sidebar.slider('fz:入力周波数', 0, 100, 1)
st.sidebar.divider()
time = st.sidebar.slider('解析時間[s]',0, 50, (0, 5))
b = st.sidebar.slider('解析分解能[ms]',0, 100, 10)

# メインプログラム
if __name__ == "__main__":
    st.header("応答波形", divider='red')

    if option == '1次遅れ系':
        # 1次遅れ系
        P = tf([0, K], [T, 1])
        st.latex(r'''
                \frac{K}{Ts+1}
                ''')
    elif option == '2次遅れ系':
        # 2次遅れ系
        P = tf([0, K*W**2], [1, 2*Z*W, W**2])
        st.latex(r'''
                \frac{Kω_{n}^2}{s^2+2ζω_{n}s+ω_{n}^2}
                ''')
    elif option == '1次遅れ+積分要素':
        # 1次遅れ+積分要素
        P = tf([0, K], [T, 1, 0])
        st.latex(r'''
                \frac{K}{s(Ts+1)}
                ''')
    else:
        st.latex(r'''
                \frac{As+B}{Cs^2+Ds+E}
                ''')
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1:
            A = st.number_input('A', value=1.0)
        with c2:
            B = st.number_input('B', value=1.0)
        with c3:
            C = st.number_input('C', value=1.0)
        with c4:
            D = st.number_input('D', value=1.0)
        with c5:
            E = st.number_input('E', value=1.0)
        P = tf([A, B], [C, D, E])
    
    Td = np.arange(time[0],time[1],b/1000)
    u = np.sin(fz * Td)

    if ut == 'ステップ':
        y, t = step(P, Td)
    else :
        y, t, _ = lsim(P, u, Td, 0)

    data = go.Scatter(x=t, y=y)

    layout = go.Layout(
        width = 700,
        height = 500,
        title = dict(text=f"{option}の{ut}入力に対する応答"),
        xaxis = dict(title='時間'),
        yaxis = dict(title='ゲイン')
    )

    # フィギュアの作成
    fig1 = go.Figure(data=data, layout=layout)
    # フィギュアの表示
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.write('極', P.poles())
    with col2:
        st.write('零点', P.zeros())
    
    st.text_area("メモ",
                "・極が負側に大きくなるほど、応答が速くなる  \n"
                "   ⇨ Tが小さいほど or ωnが大きいほど、応答が速くなる  \n"
                "・極の虚部が0でない時、振動的になり、虚部が大きいはど振動が速くなる  \n"
                "   ⇨ 1次遅れは振動しない。ζが0に近いほど虚部が大きくなるため振動する。  \n"
                "・零点が負の時は安定零点＝最小位相系。正の時は不安定零点＝非最小位相系。  \n"
                "   ⇨ 不安定零点の時は、ステップ入力を加えた時に逆ぶれが生じることがある。")

    mag, phase, w = bode(P, logspace(-2,2), plot=True)

    data2 = go.Scatter(x=w, y=mag)
    data3 = go.Scatter(x=w, y=phase)

    layout2 = go.Layout(
        width = 700,
        height = 350,
        title = dict(text=f"{option}のボード線図"),
        xaxis = dict(title='周波数[rad/s]', type='log'),
        yaxis = dict(title='ゲイン[dB]')
    )
    layout3 = go.Layout(
        width = 700,
        height = 350,
        xaxis = dict(title='周波数[rad/s]', type='log'),
        yaxis = dict(title='位相[deg]')
    )

    # フィギュアの作成
    fig2 = go.Figure(data=data2, layout=layout2)
    fig3 = go.Figure(data=data3, layout=layout3)
    # フィギュアの表示
    st.plotly_chart(fig2, use_container_width=True)
    st.plotly_chart(fig3, use_container_width=True)
        

