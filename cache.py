import os.path
import cPickle as pickle
import collections
import zlib


class Cache(collections.MutableMapping):
    def __init__(self):
        self.cache = None
        self.filename = None

    def load(self, filename):
        self.filename = filename+'.cache'
        if os.path.exists(self.filename):
            f = open(self.filename, 'rb')
            self.cache = pickle.loads(zlib.decompress(f.read()))
            f.close()
        else:
            self.cache = {}
        self.dirty = False

    def save(self):
        if not self.dirty:
            return
        try:
            f = open(self.filename, 'wb')
            f.write(zlib.compress(pickle.dumps(self.cache, pickle.HIGHEST_PROTOCOL)))
            f.close()
        except Exception as e:
            print 'Could not save cache. ({e})'.format(e=e)

    def __contains__(self, key):
        return self.cache.__contains__(key)

    def __getitem__(self, key):
        return self.cache.__getitem__(key)

    def __setitem__(self, key, value):
        self.dirty = True
        self.cache.__setitem__(key, value)

    def __delitem__(self, key):
        self.cache.__delitem__(key)

    def __len__(self):
        return self.cache.__len__()

    def __iter__(self):
        return self.cache.__iter__()


cache = Cache()
