import faiss
import numpy as np
import os
import pickle

# i need to save this stuff somewhere
MY_FOLDER = os.path.dirname(__file__) + "/../vector_store"
if not os.path.exists(MY_FOLDER):
    os.makedirs(MY_FOLDER) # make it if it dont exist lol

INDEX_FILE_PATH = MY_FOLDER + "/index.faiss"
DATA_FILE_PATH = MY_FOLDER + "/chunks.pkl"

def make_the_index(vecs, text_data):
    # print("making index!!!")
    d = vecs.shape[1] # dimension size
    idx = faiss.IndexFlatIP(d)
    idx.add(vecs.astype("float32"))
    
    # write to disk
    faiss.write_index(idx, INDEX_FILE_PATH)
    
    # save text chunks so we can read them later
    f = open(DATA_FILE_PATH, "wb")
    pickle.dump(text_data, f)
    f.close()

def get_index():
    # checking if it is there
    if os.path.exists(INDEX_FILE_PATH) == False:
        return None, []
    
    i = faiss.read_index(INDEX_FILE_PATH)
    f2 = open(DATA_FILE_PATH, "rb")
    d = pickle.load(f2)
    f2.close()
    return i, d

def search_stuff(query_vec, number_of_results=4):
    # this searches for the closest matches
    ind, dat = get_index()
    if ind == None:
        return []
    if len(dat) == 0:
        return []
    
    q_arr = np.array([query_vec]).astype("float32")
    # print(q_arr)
    
    s, ids = ind.search(q_arr, min(number_of_results, len(dat)))
    
    ans = []
    # loop through results
    for val1, val2 in zip(ids[0], s[0]):
        if val1 >= 0 and val1 < len(dat):
            ans.append({"text": dat[val1], "score": float(val2)})
    return ans

def check_index():
    return os.path.exists(INDEX_FILE_PATH)

def clear_all():
    # delete everything to restart
    if os.path.exists(INDEX_FILE_PATH):
        os.remove(INDEX_FILE_PATH)
    if os.path.exists(DATA_FILE_PATH):
        os.remove(DATA_FILE_PATH)
    # done
