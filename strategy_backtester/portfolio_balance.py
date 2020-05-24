#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 21 2020

@author: Mandeep S Gill

email : msg8930@yahoo.com

"""

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pass


def portfolio_balance(portfolio, df, previous_date):
    print("Current Portfolio with Profit and Loss as on {}".format(previous_date))
    symbols = portfolio['Contract_name'].unique().tolist()
    if 'NO-TRADE-DAY' in symbols:
        symbols.remove('NO-TRADE-DAY')
    portfolio_positions_df = portfolio_positions(portfolio)
    # print(portfolio_positions_df)

    portfolio_positions_df = open_trade_positions(portfolio_positions_df)

    # print(portfolio_positions_df)
    #
    current_close_value_df = get_close_data(symbols, df)
    portfolio_positions_df = merge_df(portfolio_positions_df, current_close_value_df)
    print(portfolio_positions_df)
    r_pnl_df = realized_profit(portfolio_positions_df)
    portfolio_positions_df = merge_df(portfolio_positions_df, r_pnl_df)
    #
    unr_pnl_df = un_realized_profit(portfolio_positions_df)
    combine_positions_df = merge_df(portfolio_positions_df, unr_pnl_df)
    print(combine_positions_df)


def portfolio_positions(df):
    # print(df)
    positions = df.groupby(['Contract_name', 'Type'], as_index=False).agg({'Qty': 'sum', 'Trade_Value': 'sum'})
    positions.insert(3, 'Avg', (positions['Trade_Value'] / positions['Qty']))
    positions= positions.round(2)
    # print('Inside the sum')
    rearrange_col = ['Contract_name', 'Type', 'Qty', 'Avg', 'Trade_Value']
    positions = positions[rearrange_col]
    print(positions)
    return join_same_contract(positions)


def join_same_contract(df):
    trades = ['Long', 'Short']
    pos = {}

    for t in trades:
        temp_df = df[df['Type'] == t]
        del temp_df['Type']
        print('temp_df')
        print(temp_df)
        h_q = '{}_Qty'.format(t)
        h_a = '{}_Avg'.format(t)
        h_v = '{}_Value'.format(t)
        temp_df.columns = ['Contract_name', h_q, h_a, h_v ]
        pos[t] = temp_df

    return pos['Long'].merge(pos['Short'], on='Contract_name', how='outer').fillna(0.0)


def merge_df(df1, df2):
    return df1.merge(df2, on='Contract_name', how='outer').fillna(0.0)


def open_trade_positions(df):

    df['Open_Qty'] = abs(df['Long_Qty'] - df['Short_Qty'])
    df['Type'] = find_pending_trade_type(df)
    return df


def common_elements(lst1, lst2):
    return list(set(lst1).intersection(lst2))


# Create a function to apply to each row of the data frame
def find_pending_trade_type(df):
    """ Find the trade value according to its sign like negative number means Short type
    or positive number means Long """
    df['Type'] = df['Long_Qty'] - df['Short_Qty']

    return df['Type'].map(lambda val: check_trade_type(val))


def check_trade_type(num):
    if num > 0:
        return 'Long'
    elif num == 0:
        return 'None'
    else:
        return 'Short'


def un_realized_profit(df):
    unr_pnl_lst = []
    for row in df.itertuples():
        cn = row.Contract_name
        if row.Type == 'Long':
            val = (row.Long_Qty - row.Squared_Qty) * (row.Close - row.Long_Avg)
            val = round(val, 2)
            unr_pnl_lst.append([cn, val])
        else:
            val = (row.Short_Qty - row.Squared_Qty) * (row.Short_Avg - row.Close)
            val = round(val, 2)
            unr_pnl_lst.append([cn, val])

    return pd.DataFrame(unr_pnl_lst, columns=['Contract_name', 'UnRealized_PnL'])


def realized_profit(df):
    closed_contract_filter = (df['Long_Qty'] > 0) & (df['Short_Qty'] > 0)
    closed_df = df[closed_contract_filter]
    lists = []
    for row in closed_df.itertuples():
        cn = row.Contract_name
        if row.Long_Qty < row.Short_Qty:
            qty = row.Long_Qty
            pnl = round(row.Long_Qty * (row.Short_Avg - row.Long_Avg), 2)
            lists.append([cn, qty, pnl])
        else:
            qty = row.Short_Qty
            pnl = round(row.Short_Qty * (row.Short_Avg - row.Long_Avg), 2)
            lists.append([cn, qty, pnl])

    return pd.DataFrame(lists, columns=['Contract_name', 'Squared_Qty', 'Realized_PnL'])


def get_close_data(symbols, df):
    sp = symbol_to_strike_price(symbols)
    closes = []
    temp = df[df['Strike Price'].isin(sp)]
    temp = temp[['Strike Price', 'CE Close', 'PE Close']].reset_index()

    for item in symbols:

        lst = item.split('-')

        sp_filter = temp['Strike Price'] == float(lst[1])

        val = temp.loc[sp_filter, '{} Close'.format(lst[2])].values[0]

        closes.append([item, val])

    return pd.DataFrame(closes, columns=['Contract_name', 'Close'])


def symbol_to_strike_price(sym):
    sp = []
    for elem in sym:
        sp.append(elem.split('-')[1])
    return sp