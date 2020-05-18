#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 14 2020

@author: Mandeep S Gill

email : msg8930@yahoo.com

"""
import os.path

from re import compile as re_compile

try:
    import pandas as pd
except ImportError:
    pass

from config import TRADE_BOOK_COL, lot_size, symbol, expiry_date


def open_file(filename):
    try:
        return pd.read_csv(filename)
    except:
        print("{} File is Missing.. Please check the file".format(filename))


def trade_book(sym, exp):
    file_path = "Data/{}-TRDBOOK-{}.csv".format(sym, exp)
    if os.path.exists(file_path):
        return open_file(file_path)
    else:
        df = pd.DataFrame(columns=TRADE_BOOK_COL)
        return df


def save_df(df, sym, exp):
    file_path = "Data/{}-TRDBOOK-{}.csv".format(sym, exp)
    print("Trade Book is Saving at this location {}".format(file_path))
    df.to_csv(file_path, index=False)


def list_to_df(lst):
    # df col. = Contract Name,Open Date,Qty,Type,Adj. Cost
    # lst ['Long', 'CE', 210.0, 1.2, 1, '2019-04-26']
    contract_name = symbol + str(lst[2]) + lst[1]
    date = lst[5]
    qty = lst[4] * lot_size
    ty = lst[0]
    adj_cost = qty * lst[3]

    lst_update = [contract_name, date, qty, ty, adj_cost]

    return pd.DataFrame([lst_update], columns=TRADE_BOOK_COL)


def exit_loop(val):
    if val and val[0].upper() == 'E':
        return True


def rename_col_names(df, val):
    headers = {'Qty': '{} Qty'.format(val), 'Adj. cost': '{} Adj. cost'.format(val)}
    return df.rename(columns=headers)


def portfolio_start_balance(portfolio, start_date):
    print("Current Portfolio with Profit and Loss as on {}".format(start_date))
    symbols = portfolio['Contract name'].unique()
    print (symbols)
    current_positions = portfolio
    print("positions__future", current_positions)
    long_positons = portfolio[portfolio['Type'] == 'Long'].groupby(['Contract name'])['Qty', 'Adj. cost'].sum()
    long_positons = rename_col_names(long_positons, 'Long')
    print("Longs", long_positons)

    short_positons = portfolio[portfolio['Type'] == 'Short'].groupby(['Contract name'])['Qty', 'Adj. cost'].sum()
    short_positons = rename_col_names(short_positons, 'Short')
    print("Shorts", short_positons)
    combine_positions = pd.concat([long_positons, short_positons], axis=1, sort=False).fillna(0.0)
    # combine_positions = pd.merge(long_positons, short_positons, left_on='Contract name', right_on='Contract name')
    print(combine_positions.reset_index().rename(columns={'index': 'Contract name'}))
    # sales = sales.reset_index()
    # print("Sales reset", sales)
    #
    # positions_no_change = positions_before_start[~positions_before_start['Contract name'].isin(sales['Contract name'].unique())]
    # print("positions_no_change", positions_no_change)
    # adj_positions_df = pd.DataFrame()

    # for sale in sales.iterrows():
    #     print("sale in loop", sale)
    #     adj_positions = position_adjust(positions_before_start, sale)
    #     adj_positions_df = adj_positions_df.append(adj_positions)
    # adj_positions_df = adj_positions_df.append(positions_no_change)
    # adj_positions_df = adj_positions_df.append(future_positions)
    # print("adj_positions_df", adj_positions_df)
    # adj_positions_df = adj_positions_df[adj_positions_df['Qty'] > 0]
    # adj_positions_df = adj_positions_df.groupby('Symbol').agg(
    #     {'Qty': 'sum', 'Adj cost': 'sum', 'Adj cost per share': 'mean'})
    # # df.groupby('A').agg({'B': ['min', 'max'], 'C': 'sum'})
    # print("adj_positions_df after qty", adj_positions_df)
    # return adj_positions_df


def trading_days(df, col="Date"):
    days = []
    try:
        days_row = df['{}'.format(col)].tolist()
        [days.append(x) for x in days_row if x not in days]
    except:
        days =[]
    return days


def order_place(data_df):

    return validate_input(data_df)


def validate_input(data_df):
    uprice = data_df['Underlying'].values[0]
    print("Underlying Price: ", uprice)
    get_available_strike_price(data_df)
    while True:
        print("Enter the Order in given format Long/Short Call/Put Strike_Price Premium Lot_Qty (long call 210 12.0 1) ")
        inp = list(input().split())

        cond = [inp, len(inp) == 5]

        if all(cond):
            validate_or_update_values(inp, data_df)
            print("your in trade")
            print(inp)
            return inp


def get_available_strike_price(df):
    strike_price_range = df['Strike Price'].tolist()
    print("Available Strike Price: ")
    print(strike_price_range)
    return strike_price_range


def validate_or_update_values(inp_lst, data_df):
    validate_trade_value(inp_lst)
    validate_option_value(inp_lst)
    validate_strike_price_value(inp_lst, data_df)
    validate_premium_value(inp_lst, data_df)
    validate_lot_qty_value(inp_lst)


def validate_trade_value(lst):
        if lst and lst[0][0].upper() == 'L':
            lst[0] = 'Long'
        elif lst and lst[0][0].upper() == 'S':
            lst[0] = 'Short'
        else:
            while True:
                res = message("Updated trade type:")
                if res and res[0].upper() == 'L':
                    lst[0] = 'Long'
                    break
                elif res and res[0].upper() == 'S':
                    lst[0] = 'Short'
                    break


def validate_option_value(lst):
    if lst and lst[1][0].upper() == 'C':
        lst[1] = 'CE'
    elif lst and lst[1][0].upper() == 'P':
        lst[1] = 'PE'
    else:
        while True:
            res = message("Updated Option type:")
            if res and res[1].upper() == 'C':
                lst[1] = 'CE'
                break
            elif res and res[0].upper() == 'P':
                lst[1] = 'PE'
                break


def validate_strike_price_value(lst, data_df):
    sp_lst = get_available_strike_price(data_df)
    if is_inp_str_number(lst[2]):
        if is_strike_price_available(lst[2], sp_lst):
            lst[2] = float(lst[2])
        else:
            while True:
                res = message("Updated Strike Price:")
                if is_inp_str_number(res):
                    if is_strike_price_available(res, sp_lst):
                        lst[2] = float(res)
                        break


def validate_premium_value(lst, data_df):
    if is_inp_str_number(lst[3]):
        if is_premium_available(lst, lst[3], data_df):
            lst[3] = float(lst[3])
        else:
            while True:
                res = message("Updated Premium Price:")
                if is_inp_str_number(res):
                    if is_premium_available(lst, res, data_df):
                        lst[3] = float(res)
                        break


def validate_lot_qty_value(lst):
    if is_inp_str_number(lst[4]):
        lst[4] = int(lst[4])
    else:
        while True:
            res = message("Updated Lot qty:")
            if is_inp_str_number(res):
                lst[4] = int(res)
                break


comp = re_compile("^\d+?\.\d+?$")


def is_inp_str_number(s):
    """ Returns True is string is a number. """
    if not s:
        return False
    if comp.match(s) is None:
        return s.isdigit()
    return True


def is_strike_price_available(sp, lst):
    if float(sp) in lst:
        return True


def message(msg):
    return input("Enter {} :".format(msg))


def is_premium_available(lst, val, data_df):

    filter_sp_row = data_df['Strike Price'] == lst[2]
    col_lst = ['High', 'Low'] if lst[1] == 'CE' else ['PE High', 'PE Low']

    premium_range = data_df.loc[filter_sp_row, col_lst].values[0]
    print(premium_range)

    if premium_range[1] <= float(val) <= premium_range[0]:
        return True
    return False

