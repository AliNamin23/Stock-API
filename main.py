import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import requests
import datetime

options_dict = {1:'open', 2:'high', 3:'low', 4:'close', 5:'volume'}
graph_labels = {1:"Opening Price", 2:"Day High", 3:"Day Low", 4:"Closing Price", 5:"Stock Volume"}

prompt = """\n ---- OPTION SELECTION ----
Select the information you with to view
1) Opening Price
2) Day High
3) Day Low
4) Close Price
5) Volume of Shares
--> """

helper_prompt = """ ------ INVALID INPUT ------
Input should be separated by commmas only
Eample:
For Day High and Day Low input: 2, 3"""

def get_wanted_stocks():
    get_data = True
    stocks = []

    print(" ---- Stock Selection ----")
    print("Enter ticker symbol for each stock you want to view.\nEnter 'done' when finished.\n")

    while get_data:
        inp = input("Enter Ticker Symbol: ").strip()
        if inp.lower() == 'done' or inp.lower() == "":
            get_data = False
        elif inp.upper() not in stocks:
            stocks.append(inp.upper())

    return stocks

def get_options():
    options = ""
    over_time = False
    start_date = None
    end_date = None
    while True:
        valid = True
        inp = input(prompt).strip()
        inp = inp.replace(" ", "")

        options = inp.split(',')
        for x in options:
            if x not in ['1', '2', '3', '4', '5']:
                print(helper_prompt)
                valid = False
                break

        if valid:
            break

    options = list(set(options))

    while True:
        valid = True
        inp = input("\nWould you like to view stock data over time? (y/n): ").strip()

        if inp.lower() == 'y' or inp.lower() == 'yes':
            over_time = True
        elif inp.lower() == 'n' or inp.lower() == 'no':
            over_time = False
        else:
            valid = False

        if valid:
            break

    if over_time:
        print("\n ---- DATE SELECTION ----")
        while True:
            valid = True
            print("Enter dates with format dd/mm/yyyy")
            inp = input("Start date: ").strip()

            try:
                d, m, y = inp.split('/')
                start_date = datetime.datetime(int(y), int(m), int(d))
            except ValueError:
                print("--- Invalid Date ---\n")
                valid = False

            if valid == False:
                continue

            print("\nEnter end date. Leave blank for current date.")
            inp = input("End date: ").strip()

            if inp == "":
                end_date = datetime.datetime.now()
            else:
                try:
                    d, m, y = inp.split('/')
                    end_date = datetime.datetime(int(y), int(m), int(d))
                except ValueError:
                    print("--- Invalid date ---\n")
                    valid = False

            if valid == False:
                continue

            if start_date > end_date:
                print("Start date must be before end date.\n")
                valid = False

            if valid:
                break

    return (options, start_date, end_date)

def retrieve_data(ticker, start_date, end_date):
    request_url = "https://api.intrinio.com/prices"
    query_params = {
        'identifier': ticker,
        'api_key': 'OmFlOWI5NTA2OWJmMWYyYjU3MDFjZDU4NjMwNjRhNDcz',
        'start_date': start_date.strftime("%Y-%m-%d"),
        'end_date': end_date.strftime("%Y-%m-%d"),
        'page_number': 1
    }

    response = requests.get(request_url, params=query_params)
    if response.status_code == 401: print("API Error. Try again."); exit()

    unwanted_cols = ['ex_dividend', 'split_ratio', 'adj_factor', 'adj_open', 'adj_high', 'adj_low', 'adj_close', 'adj_volume']

    json_resp = response.json()

    total_pages = json_resp['total_pages']

    data_frames = []

    if json_resp['data'] == []:
        raise ValueError("Stock doesn't exist")

    stock_data = pd.DataFrame(json_resp['data']).drop(unwanted_cols, axis=1)

    stock_data['date'] = pd.to_datetime(stock_data['date'])

    data_frames.append(stock_data)

    while json_resp['current_page'] < total_pages:
        query_params['page_number'] += 1

        response = requests.get(request_url, params=query_params)
        if response.status_code == 401: print("API Error. Try again."); exit()

        json_resp = response.json()
        data = pd.DataFrame(json_resp['data']).drop(unwanted_cols, axis=1)
        data['date'] = pd.to_datetime(data['date'])

        data_frames.append(data)

    stocks_data = pd.concat(data_frames)

    return stocks_data



def get_all_stock_data(stocks, start_date, end_date):
    stock_data = {}
    for ticker in stocks:
        try:
            stock_data[ticker] = retrieve_data(ticker, start_date, end_date)
        except ValueError:
            print(" ---- Error: Invalid Ticker Name ----")
            print("Skipping ", ticker, " because it is not valid.")

    return stock_data

def view_dated_stock_data(stocks, start_date, end_date, options):
    stock_data = get_all_stock_data(stocks, start_date, end_date)

    print(" ---- STOCK SUMMARIES BETWEEN ", start_date.strftime("%d/%m/%Y"), end_date.strftime("%d/%m/%Y"), " ----")
    print("----------------------------")
    for ticker in stock_data.keys():
        current_stock = stock_data[ticker]
        stock_desc = current_stock.describe()

        print("|" + ticker + "|")
        print("----------------------------")

        for i, option in enumerate(options):
            option = int(option)
            print("\t" + ticker + " " + graph_labels[option])
            print("----------------------------")
            print("Minimum: ", stock_desc[options_dict[option]]['min'])
            print("Maximum: ", stock_desc[options_dict[option]]['max'])
            print("Average: ", stock_desc[options_dict[option]]['mean'])
            print("Standard Deviation: ", stock_desc[options_dict[option]]['std'])
            print("----------------------------")

            plt.figure(i)
            plt.title(graph_labels[option] + " for stocks between " + start_date.strftime("%d/%m/%Y") + " and " + end_date.strftime("%d/%m/%Y"))
            plt.plot(current_stock['date'], current_stock[options_dict[option]], label=ticker)
            plt.ylabel(graph_labels[option])
            plt.xlabel("Date")
            dateFmt = mdates.DateFormatter('%d %B %y')
            plt.axes().xaxis.set_major_formatter(dateFmt)
            plt.axes().grid(True)
            plt.xticks(rotation='vertical')
            plt.tight_layout()
            plt.axes().legend()
        print("----------------------------")

    print(" ---- Displaying Stock Comparison ----")
    plt.show()

def view_undated_stock_data(stocks, options):
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=7)

    stock_data = get_all_stock_data(stocks, start_date, end_date)

    print(" ---- TODAY'S STOCK INFORMATION ----")
    for ticker in stock_data.keys():
        print("----------------------------")
        print("|" + ticker + "|")
        print("----------------------------")

        for option in options:
            option = int(option)
            print(graph_labels[option], ": ", stock_data[ticker][options_dict[option]][0])
        print("----------------------------")

    print(" ---- Displaying Stock comparison for current week ----")

    for ticker in stock_data.keys():
        for i, option in enumerate(options):
            option = int(option)
            plt.figure(i)
            plt.title(graph_labels[option] + " of stocks for this week")
            plt.plot(stock_data[ticker]['date'], stock_data[ticker][options_dict[option]], label=ticker)
            plt.ylabel(graph_labels[option])
            plt.xlabel("Date")
            dateFmt = mdates.DateFormatter('%d %B %y')
            plt.axes().xaxis.set_major_formatter(dateFmt)
            plt.axes().grid(True)
            plt.xticks(rotation='vertical')
            plt.tight_layout()
            plt.axes().legend()

    plt.show()

if __name__ == '__main__':
    stocks = get_wanted_stocks()
    options = get_options()
    if options[1] == None:
        view_undated_stock_data(stocks, options[0])
    else:
        view_dated_stock_data(stocks, options[1], options[2], options[0])

    print(" ---- Exiting Program ----")
