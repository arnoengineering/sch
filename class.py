import numpy as np


class EngClass:
    def __init__(self, name):
       self.n = name
       self.op = {'assign':{'val':[], 'weight':10}, }

    def val(self,ty):  # todo get set
        if 'func' in self.op[ty]:
            return self.op[ty]['func'](self.op[ty]['val'])
        else:
            return np.mean(self.op[ty]['val'])

    def val_over(self):  # todo proopertiy, satic class
        self.weighted_sum()

    def weighted_sum(self, x=None,y=None):
        if x is not None:
            x = np.array(self.val(k) for k in self.op.keys())
            y = np.array(k['weight'] for k in self.op.values())
            
        return np.sum(x*y)/np.sum(y)

    def drop_n(self,n,val=None):
        def nn(v2):
            return np.mean(np.max(np.sort(v2)[:-n]))

        if val is None:
            return nn
        else:
            return nn(val)
