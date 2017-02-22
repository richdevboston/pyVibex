import pandas as pd
from os import listdir
from os.path import isfile, join
from math import exp
import sys


# Constant values
m_settlement_day = 1005  # Minutes from midnight until 16:45
minutes_per_day = 1440
minutes_per_year = 525600

'''
VIX calculations are made choosing the first expiry which is at least 23 days
away, and the next expiry. IBEX does not have weekly options, so 23 days is just
too much, since the next-term expiry when there are 22 days to the first expiry
then the next-term is almost 3 months away, and nobody is trading it yet
'''
min_dist_to_near_term = pd.tslib.Timedelta(days=13)

# Load all historical files data
hist_folder = 'meff_historical_data'
hist_files = [f for f in listdir(hist_folder) if isfile(join(hist_folder, f))]

# Load each file data
column_names = ['date', 'subcode', 'cfi_code', 'strike', 'expiration', 'bid',
    'ask', 'open_interest']
for file in hist_files:
    data = pd.read_csv(join(hist_folder, file), sep=';', decimal=',',
        header=None, names=column_names, usecols=[0, 3, 4, 5, 6, 7, 8, 17],
        parse_dates=[0, 4])
    # Merge bid and ask into midpoint
    data['midpoint'] = (data.bid + data.ask) / 2
    del data['bid']
    del data['ask']
    # Filter to get only options, and classify by type
    data = data[(data.strike > 0)]
    data['is_call'] = data.apply(
        lambda row: 'OPE' not in row['cfi_code'], axis=1)
    del data['cfi_code']
    # Get unique dates
    dates = pd.to_datetime(pd.unique(data.date))

    # Iterate through them to calculate Volatility for the Index in that date
    for date in dates:
        try:
            # Get near term options
            near_term = data[(data.date == date) &
                (data.expiration - date > min_dist_to_near_term)]
            near_term = near_term.sort_values('expiration', ascending=True)
            near_term_exp = near_term.expiration.iloc[0]
            near_term = near_term[(near_term.expiration == near_term_exp)]

            print(near_term)
            # Get next term options
            next_term = data[(data.date == date) &
                (data.expiration > near_term_exp)]
            next_term = next_term.sort_values('expiration', ascending=True)
            next_term_exp = next_term.expiration.iloc[0]
            next_term = next_term[(next_term.expiration == next_term_exp)]

            # Get the strike with less difference between call and put midpoints
            # for each expiry
            near_term['diff'] = near_term[near_term['strike'].isin(
                near_term.loc[near_term.groupby('strike')['midpoint']
                    .diff().abs() > 0, 'strike'])
                ].groupby('strike')['midpoint'].diff().abs()
            min_diff_near_term = near_term.loc[near_term.dropna()['diff'].idxmin()]
            next_term['diff'] = next_term[next_term['strike'].isin(
                next_term.loc[next_term.groupby('strike')['midpoint']
                    .diff().abs() > 0, 'strike'])
                ].groupby('strike')['midpoint'].diff().abs()
            min_diff_next_term = next_term.loc[next_term.dropna()['diff'].idxmin()]

            # Determine total minutes in the days between current day and
            # expiration dates
            days_left_near = (near_term_exp - date).days
            T_1 = ((m_settlement_day + (days_left_near * minutes_per_day)) /
                minutes_per_year)
            days_left_next = (next_term_exp - date).days
            T_2 = ((m_settlement_day + (days_left_next * minutes_per_day)) /
                minutes_per_year)

            # Determine F for each expiry
            R = 0.02 #TODO
            F_1 = (min_diff_near_term['strike']
                + exp(R * T_1) * min_diff_near_term['diff'])
            F_2 = (min_diff_next_term['strike']
                + exp(R * T_2) * min_diff_next_term['diff'])
            print(F_1, F_2)

            # Get the strike price immediately below the forward index level F
            K0_1 = near_term.loc[near_term[near_term.strike < F_1].strike.idxmax()]['strike']
            K0_2 = next_term.loc[next_term[next_term.strike < F_1].strike.idxmax()]['strike']
            print(K0_1, K0_2)

            # Now, we iterate put strikes from K0 down, ignoring those with
            # bid = 0, and stopping when 2 consecute strikes have bid = 0
            sorted_call_near_term = near_term[(near_term.strike <= K0_1) & (near_term.is_call == False)].sort_values(by='strike', ascending=False)
            call_near_term = near_term[sorted_call_near_term[(pd.rolling_sum((sorted_call_near_term == 0), window=2) == 2)].first_valid_index() + 1:]
            sorted_put_near_term = near_term[(near_term.strike >= K0_1) & (near_term.is_call)].sort_values(by='strike', ascending=True)
            put_near_term = near_term[sorted_put_near_term[(pd.rolling_sum((sorted_put_near_term == 0), window=2) == 2)].first_valid_index() + 1:]
            sorted_call_next_term = next_term[(next_term.strike <= K0_2) & (next_term.is_call == False)].sort_values(by='strike', ascending=False)
            call_next_term = next_term[sorted_call_next_term[(pd.rolling_sum((sorted_call_next_term == 0), window=2) == 2)].first_valid_index() + 1:]
            sorted_put_next_term = next_term[(next_term.strike >= K0_2) & (next_term.is_call)].sort_values(by='strike', ascending=True)
            print(sorted_put_next_term)
            put_next_term = next_term[sorted_put_next_term[(pd.rolling_sum((sorted_put_next_term == 0), window=2) == 2)].first_valid_index() + 1:]

            # Now we get volatility for each one of them

        except Exception as e:
            tb = sys.exc_info()[2]
            print('[ERROR, line ' + str(tb.tb_lineno) + '] ' + str(e))
            #print date
            #print near_term, next_term
            sys.exit()
    break
