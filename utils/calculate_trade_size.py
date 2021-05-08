import sys

def calculate_trade_size(acceptable_PERC_loss, last_close):
    trade_size = 200 / (acceptable_PERC_loss * last_close)
    return trade_size

if __name__ == '__main__':
    acceptable_PERC_loss = float(sys.argv[1])
    last_close = float(sys.argv[2])
    print(calculate_trade_size(acceptable_PERC_loss, last_close))
