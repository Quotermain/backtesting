from os import listdir
import pickle
import subprocess

from time import sleep

PRICES_PATH = '/mnt/tick_prices/'
ALL_TICKERS = [file_name.split('.')[0] for file_name in listdir(PRICES_PATH)]

result = []
def run(ticker):
    bashCommand = f"python main.py {ticker}"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print(output.decode('utf-8'))
    result.append(output)

if __name__ == '__main__':
    for ticker in ALL_TICKERS:
        try:
            run(ticker)
        except Exception as e:
            print(e)
            continue
    with open('result.pickle', 'wb') as file:
        pickle.dump(result, file)
