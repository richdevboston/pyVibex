#! /usr/bin/env python
# -*- coding: utf-8 -*
import vollib.black_scholes as bs
import vollib.black_scholes.implied_volatility as iv
import vollib.black_scholes.greeks.analytical as gk
from datetime import date, datetime
from argparse import ArgumentParser


if __name__ == '__main__':
    # Configure the command line options
    parser = ArgumentParser()
    parser.add_argument('-k', '--strike', type=float, required=True,
                        help='[Required] Option strike')
    parser.add_argument('-s', '--underlying_price', type=float, required=True,
                        help='[Required] Current price of option\'s underlying')
    parser.add_argument('-t', '--expiration_date', type=str, required=True,
                        help='[Required] Option expiration date. Required format: ddmmyyyy')
    parser.add_argument('-r', '--risk_free_rate', type=float, required=True,
                        help='[Required] Risk free rate. Example: 0.01')
    parser.add_argument('-p', '--option_price', type=float, required=True,
                        help='[Required] Current option price')
    parser.add_argument('-ri', '--right', type=str, required=True,
                        help='[Required] Option right (C for call, P for Put)')
    config = parser.parse_args()
    
    last_price = config.option_price
    K = config.strike
    S = config.underlying_price  # underlying_price
    opt_date = datetime.strptime(config.expiration_date, "%d%m%Y").date()
    t = (opt_date - date.today()).days / 365.  # time to expiration (in years)
    r = config.risk_free_rate
    flag = config.right.lower()
    
    if flag != 'c' and flag != 'p':
        print('ERROR: flag shall be \'C\' or \'P\'')
    else:
        sigma = iv.implied_volatility(last_price, S, K, t, r, flag)
        delta = gk.delta(flag, S, K, t, r, sigma)
        gamma = gk.gamma(flag, S, K, t, r, sigma)
        theta = gk.theta(flag, S, K, t, r, sigma)
        vega = gk.vega(flag, S, K, t, r, sigma)
        
        print('Delta: ' + str(delta))
        print('Gamma: ' + str(gamma))
        print('Theta: ' + str(theta) + ' --> (annual): ' + str(theta * 365))
        print('Vega: ' + str(vega))
        print('IV: ' + str(sigma))