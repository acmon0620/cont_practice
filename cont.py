import plotly.graph_objects as go
import numpy as np
from control.matlab import *
import streamlit as st

st.header("応答波形確認", divider='red')

footer_text = "Ver.0.03"

st.markdown(
    f"""
    <style>
    .footer {{
        position: fixed;
        left: 92%;
        bottom: 0%;
        width: 8%;
        background-color: #f5f5f5;
        color: #000;
        text-align: center;
        padding: 10px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    f"""
    <div class="footer">
        {footer_text}
    </div>
    """,
    unsafe_allow_html=True
)

# streamlitの表示用リストとタブ
tab1, tab2 = st.tabs(['制御対象P', '制御器K'])
option_p = ['1次遅れ系','1次遅れ+積分要素','2次遅れ系','任意']
option_k = ['P制御','PD制御','PID制御']
ulist = ['ステップ','正弦波']

# サイドバーの設定
with st.sidebar:
    ut = st.selectbox('入力設定', ulist)
    st.divider()
    fz = st.slider('正弦波入力の周波数', 0, 100, 1)
    st.divider()
    time = st.slider('解析時間[s]',0, 50, (0, 5))
    b = st.slider('解析分解能[ms]',0, 100, 10)

# 時間と正弦波入力を生成
Td = np.arange(time[0],time[1],b/1000)
u = np.sin(fz * Td)

# 伝達関数Pの生成
def Transfunc(optionp):
    if optionp == '1次遅れ系':
        # 1次遅れ系
        P = tf([0, K], [T, 1])
        st.latex(r'''
                P(s)=\frac{K}{Ts+1}
                ''')
    elif optionp == '2次遅れ系':
        # 2次遅れ系
        P = tf([0, K*W**2], [1, 2*Z*W, W**2])
        st.latex(r'''
                P(s)=\frac{Kω_{n}^2}{s^2+2ζω_{n}s+ω_{n}^2}
                ''')
    elif optionp == '1次遅れ+積分要素':
        # 1次遅れ+積分要素
        P = tf([0, K], [T, 1, 0])
        st.latex(r'''
                P(s)=\frac{K}{s(Ts+1)}
                ''')
    else:
        st.latex(r'''
                P(s)=\frac{As+B}{Cs^2+Ds+E}
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
    return P

# PID制御器の生成
def PIDcont(optionk, kp, kd, ki):
    if optionk == "P制御":
        K = tf([0, kp],[0,1])
    elif optionk == "PD制御":
        K = tf([kd, kp],[0,1])
    else:
        K = tf([kd, kp, ki],[1,0])
    return K

# メインプログラム
if __name__ == "__main__":
    with tab1:
        with st.expander("### モデルの伝達関数を設定", expanded=False):
            optionp = st.selectbox('モデル設定', option_p)
            c1,c2 = st.columns(2)
            with c1:
                K = st.slider('K:ゲイン', -1.00, 2.00, 1.00)
                T = st.slider('T:時定数', -1.00, 2.00, 1.00)
            with c2:
                Z = st.slider('ζ:減衰係数', -1.00, 2.00, 1.00)
                W = st.slider('Wn:固有角周波数', -10.00, 10.00, 1.00)

        with st.expander("### ブロック図", expanded=False):
            st.image('pstep.png', use_column_width=True)
        
        P = Transfunc(optionp)

        if ut == 'ステップ':
            y, t = step(P, Td)
        else :
            y, t, _ = lsim(P, u, Td, 0)

        # データ作成
        data1 = go.Scatter(x=t, y=y)
        layout = go.Layout(
            width = 700,
            height = 500,
            title = dict(text=f"{optionp}の{ut}入力に対する応答"),
            xaxis = dict(title='時間'),
            yaxis = dict(title='ゲイン')
        )
        # フィギュアの作成
        fig1 = go.Figure(data=data1, layout=layout)
        # フィギュアの表示
        st.plotly_chart(fig1, use_container_width=True)

        with st.expander("### ステップ応答における性能指標", expanded=False):
            infop = stepinfo(P, SettlingTimeThreshold=0.05)
            st.write(infop)
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
            title = dict(text=f"{optionp}のボード線図"),
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
    
    with tab2:
        with st.expander("### 制御器の設定", expanded=False):
            optionk = st.selectbox('制御器の種類', option_k)
            c1,c2,c3 = st.columns(3)
            with c1:
                Kp = st.slider('比例ゲイン', -1.00, 5.00, 1.00)
            with c2:
                Kd = st.slider('微分ゲイン', -1.00, 1.00, 1.00)
            with c3:
                Ki = st.slider('積分ゲイン', -1, 30, 1)

        K = PIDcont(optionk, Kp, Kd, Ki)
        G = feedback(P*K, 1)    # 閉ループ

        if ut == 'ステップ':
            y, t = step(G, Td)
        else :
            y, t, _ = lsim(G, u, Td, 0)

        # データ作成
        datak1 = go.Scatter(x=t, y=y)
        layout = go.Layout(
            width = 700,
            height = 500,
            title = dict(text=f"{optionk}の{ut}入力に対する応答"),
            xaxis = dict(title='時間'),
            yaxis = dict(title='ゲイン')
        )
        # フィギュアの作成
        fig1 = go.Figure(data=datak1, layout=layout)
        # フィギュアの表示
        st.plotly_chart(fig1, use_container_width=True)

        with st.expander("### ステップ応答における性能指標", expanded=False):
            infop = stepinfo(G, SettlingTimeThreshold=0.05)
            st.write(infop)
            col1, col2 = st.columns(2)
            with col1:
                st.write('極', G.poles())
            with col2:
                st.write('零点', G.zeros())

        mag, phase, w = bode(G, logspace(-2,2), plot=True)

        datak2 = go.Scatter(x=w, y=mag)
        datak3 = go.Scatter(x=w, y=phase)

        layout2 = go.Layout(
            width = 700,
            height = 350,
            title = dict(text=f"{optionp}のボード線図"),
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
        fig2 = go.Figure(data=datak2, layout=layout2)
        fig3 = go.Figure(data=datak3, layout=layout3)
        # フィギュアの表示
        st.plotly_chart(fig2, use_container_width=True)
        st.plotly_chart(fig3, use_container_width=True)