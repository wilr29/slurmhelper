'''
Miscellaneous helper functions.
'''

# Lil' helper function from stackoverflow
# source: https://stackoverflow.com/questions/752308/split-list-into-smaller-lists-split-in-half
def split_list(alist, wanted_parts=1):
    '''
    Split a list into a given number of parts. Used to divvy up jobs evenly.
    :param alist: list o' jobs
    :param wanted_parts: how many chunks we want
    :return: list o' lists
    '''
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts]
             for i in range(wanted_parts) ]