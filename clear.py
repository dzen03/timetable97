import pickle

gk = {"today_hash": '', "tomorrow_hash": ''}
pickle.dump(gk, open("save.p", "wb"))
