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

from strategy_backtester.config import trade_book, trade_book_col, \
    find_avg_and_add_col_to_df_col, trade_types, open_trade_positions_col, sum_qty_trade_value_col


def portfolio_balance(portfolio, df, previous_date):
    print("Current Portfolio with Profit and Loss as on {}".format(previous_date))
    symbols = get_unique_contracts_lst(portfolio)
    if 'NO-TRADE-DAY' in symbols:
        symbols.remove('NO-TRADE-DAY')
    portfolio_positions_df = portfolio_positions(portfolio)
    # print(portfolio_positions_df)

    portfolio_positions_df = open_trade_positions(portfolio_positions_df)

    # print(portfolio_positions_df)
    #
    current_close_value_df = get_close_data(symbols, df)
    portfolio_positions_df = merge_df(portfolio_positions_df, current_close_value_df)
    # print(portfolio_positions_df)
    r_pnl_df = realized_profit(portfolio_positions_df)
    portfolio_positions_df = merge_df(portfolio_positions_df, r_pnl_df)
    #
    unr_pnl_df = un_realized_profit(portfolio_positions_df)
    combine_positions_df = merge_df(portfolio_positions_df, unr_pnl_df)
    print(combine_positions_df)


def get_unique_contracts_lst(portfolio_df):
    return portfolio_df[trade_book['Contract_name']].unique().tolist()


def sort_df_with_column(df, column):

    return df.sort_values(by=column).reset_index(drop=True)


def portfolio_positions(trade_df):

    positions = sum_qty_and_trade_value_contracts(trade_df)

    return display_buy_and_sell_side_by_side(positions)


def sum_qty_and_trade_value_contracts(trade_df):
    c = trade_df.groupby([trade_book['Contract_name'], trade_book['Type']], as_index=False)\
        .agg({'Qty': 'sum', 'Trade_value': 'sum'}, index=False)

    return c[sum_qty_trade_value_col]


def find_avg_and_add_col_to_df(combine_df):
    combine_df.insert(3, 'Avg', (combine_df[trade_book['Trade_value']] / combine_df[trade_book['Qty']]))

    combine_df.round(2)
    return combine_df[find_avg_and_add_col_to_df_col]


def display_buy_and_sell_side_by_side(df):

    pos = {}

    for t in trade_types:
        temp_df = df[df[trade_book['Type']] == t]
        del temp_df[trade_book['Type']]
        h_q = '{}_Qty'.format(t)
        h_a = '{}_Avg'.format(t)
        h_v = '{}_Value'.format(t)
        temp_df.columns = [trade_book['Contract_name'], h_q, h_a, h_v]
        pos[t] = temp_df

    return pos['Buy'].merge(pos['Sell'], on='Contract_name', how='outer').fillna(0.0)


def merge_df(df1, df2):
    return df1.merge(df2, on='Contract_name', how='outer').fillna(0.0)


def open_trade_positions(df):
    op_df = pd.DataFrame()
    op_df[trade_book['Contract_name']] = df[trade_book['Contract_name']]
    op_df['Open_Qty'] = abs(df['Buy_Qty'] - df['Sell_Qty'])
    op_df['Type'] = find_pending_trade(df)
    return op_df[open_trade_positions_col]


def common_elements(lst1, lst2):
    return list(set(lst1).intersection(lst2))


# Create a function to apply to each row of the data frame
def find_pending_trade(df):
    """ Find the trade value according to its sign like negative number means Sell type
    or positive number means Buy """
    df['Type'] = df['Buy_Qty'] - df['Sell_Qty']

    return df['Type'].map(lambda val: trade_type_conversion(val))


def trade_type_conversion(num):
    if num < 0:
        return 'Buy'
    elif num == 0:
        return 'None'
    else:
        return 'Sell'


def un_realized_profit(df):
    unr_pnl_lst = []
    for row in df.itertuples():
        cn = row.Contract_name
        if row.Type == 'Buy':
            val = (row.Buy_Qty - row.Squared_Qty) * (row.Close - row.Buy_Avg)
            val = round(val, 2)
            unr_pnl_lst.append([cn, val])
        else:
            val = (row.Sell_Qty - row.Squared_Qty) * (row.Sell_Avg - row.Close)
            val = round(val, 2)
            unr_pnl_lst.append([cn, val])

    return pd.DataFrame(unr_pnl_lst, columns=['Contract_name', 'UnRealized_PnL'])


def realized_profit(df):
    closed_contract_filter = (df['Buy_Qty'] > 0) & (df['Sell_Qty'] > 0)
    closed_df = df[closed_contract_filter]
    lists = []
    for row in closed_df.itertuples():
        cn = row.Contract_name
        if row.Buy_Qty < row.Sell_Qty:
            qty = row.Buy_Qty
            pnl = round(row.Buy_Qty * (row.Sell_Avg - row.Buy_Avg), 2)
            lists.append([cn, qty, pnl])
        else:
            qty = row.Sell_Qty
            pnl = round(row.Sell_Qty * (row.Sell_Avg - row.Buy_Avg), 2)
            lists.append([cn, qty, pnl])

    return pd.DataFrame(lists, columns=['Contract_name', 'Squared_Qty', 'Realized_PnL'])


def get_close_data(symbols_lst, df):
    sp = get_strike_price_list_from_contract_names(symbols_lst)
    closes = []
    temp = df[df['Strike Price'].isin(sp)]
    temp = temp[['Strike Price', 'CE Close', 'PE Close']].reset_index()

    for item in symbols_lst:

        lst = item.split('-')

        sp_filter = temp['Strike Price'] == float(lst[1])

        val = temp.loc[sp_filter, '{} Close'.format(lst[2])].values[0]

        closes.append([item, val])

    return pd.DataFrame(closes, columns=['Contract_name', 'Close'])


def get_strike_price_list_from_contract_names(sym_lst):
    sp = []
    for elem in sym_lst:
        sp.append(float(elem.split('-')[1]))
    return sp

