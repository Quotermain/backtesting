import pickle

data_path = '../metatrader_connector/data/thresholds/open_close_5min_dif.pickle'

with open(data_path, 'rb') as file:
    open_close_5min_dif = pickle.load(file)

print(open_close_5min_dif['NVTK.MM'])
