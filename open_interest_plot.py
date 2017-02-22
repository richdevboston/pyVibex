#! /usr/bin/env python
# -*- coding: utf-8 -*
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('ggplot')


def plot_open_interest(dataframe: pd.DataFrame):
    '''
    TODO
    '''
    # Filter out strikes too OTM
    df = dataframe[(dataframe.strike > 8500) & (dataframe.strike < 10500)]
    
    # Get min and max strikes
    min_strike = int(df.strike.min())
    max_strike = int(df.strike.max())
    strikes = np.arange(min_strike, max_strike + 100, 100)
    width = 25
    
    # Separate calls from puts
    call = df[df.right == 'C']
    put  = df[df.right == 'P']
    
    # Iterate each to get ordered list of open interest per strike
    call_oi = [0] * len(strikes)
    put_oi  = [0] * len(strikes)
    for i, s in enumerate(strikes):
        oi = call[call.strike == s]
        call_oi[i] = 0 if oi.empty else int(oi.open_interest)
        oi = put[put.strike == s]
        put_oi[i] = 0 if oi.empty else int(oi.open_interest)

    fig, ax = plt.subplots()
    ax.barh(strikes, call_oi, width, color='blue', align='center', label='Calls')
    ax.barh(strikes+width, put_oi, width, color='red', align='center', label='Puts')
    ax.set(yticks=strikes+width, ylim=[min_strike, max_strike])
    ax.grid(True)
    ax.legend()

    plt.show()
