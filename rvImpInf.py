import sys
sys.path.insert(0,'/usr/local/lib/python3.7/site-packages/')
import spot
import time
from enum import Enum
import buddy

class Verdict(Enum):
    ff = 0
    tt = 1
    nf = 2
    nt= 3
    unknown = 4
    undefined = 5
    def __str__(self):
        if self.value == 0:
            return 'False'
        elif self.value == 1:
            return 'True'
        elif self.value == 2:
            return 'Unknown (but it won\'t ever be False)'
        elif self.value == 3:
            return 'Unknown (but it won\'t ever be True)'
        elif self.value == 4:
            return 'Unknown'
        else:
            return 'Undefined'

class Monitor:
    def __init__(self, ltl, ap, sim):
        eLTL = explicit_ltl(ltl, sim)
        enLTL = explicit_ltl(spot.formula('!(' + ltl + ')').negative_normal_form().to_str(), sim)
        self.__pAut = spot.translate(eLTL)
        self.__nAut = spot.translate(enLTL)
        self.__uAut = spot.translate('!'+eLTL+'&'+'!'+enLTL)
        self.__pInit, self.__pFin = self.setup(self.__pAut)
        self.__nInit, self.__nFin = self.setup(self.__nAut)
        self.__uInit, self.__uFin = self.setup(self.__uAut)
        self.__ap = ap
        self.__sim = sim
    def setup(self, aut):
        fin = set()
        states = set()
        statesAux = set()
        init = aut.get_init_state_number()
        states.add(aut.get_init_state_number())
        statesAux.add(aut.get_init_state_number())
        while statesAux:
            s0 = statesAux.pop()
            for t in aut.out(s0):
                if t.dst not in states:
                    states.add(t.dst)
                    statesAux.add(t.dst)
        for s in states:
            aut.set_init_state(s)
            if not aut.is_empty():
                fin.add(s)
        aut.set_init_state(init)
        initSet = set()
        initSet.add(init)
        return initSet, fin
    def next(self, ev):
        event = buddy.bddtrue
        for ap in self.__ap:
            if ap.startswith('!'): continue
            ind = []
            for s in self.__sim:
                if ap in s:
                    ind = s
                    break
            if not ind and ap in ev:
                a = self.__pAut.register_ap(ap+'tt')
                b = self.__pAut.register_ap(ap+'ff')
                bdda = buddy.bdd_ithvar(a)
                bddb = buddy.bdd_nithvar(b)
                event = event & bdda & bddb
            elif not ind and ap not in ev:
                a = self.__pAut.register_ap(ap+'ff')
                b= self.__pAut.register_ap(ap+'tt')
                bdda = buddy.bdd_ithvar(a)
                bddb = buddy.bdd_nithvar(b)
                event = event & bdda & bddb
            elif ind and all(elem in ev for elem in ind):
                a = self.__pAut.register_ap(ap+'tt')
                b = self.__pAut.register_ap(ap+'ff')
                bdda = buddy.bdd_ithvar(a)
                bddb = buddy.bdd_nithvar(b)
                event = event & bdda & bddb
            elif ind and all(elem not in ev for elem in ind):
                a = self.__pAut.register_ap(ap+'ff')
                b = self.__pAut.register_ap(ap+'tt')
                bdda = buddy.bdd_ithvar(a)
                bddb = buddy.bdd_nithvar(b)
                event = event & bdda & bddb
            else:
                a = self.__pAut.register_ap(ap+'tt')
                b = self.__pAut.register_ap(ap+'ff')
                bdda = buddy.bdd_nithvar(a)
                bddb = buddy.bdd_nithvar(b)
                event = event & bdda & bddb
        pInitAux = set()
        while self.__pInit:
            init = self.__pInit.pop()
            for t in self.__pAut.out(init):
                if (t.cond & event) != buddy.bddfalse and t.dst in self.__pFin:
                    pInitAux.add(t.dst)
        self.__pInit = pInitAux
        nInitAux = set()
        while self.__nInit:
            init = self.__nInit.pop()
            for t in self.__nAut.out(init):
                if (t.cond & event) != buddy.bddfalse and t.dst in self.__nFin:
                    nInitAux.add(t.dst)
        self.__nInit = nInitAux
        uInitAux = set()
        while self.__uInit:
            init = self.__uInit.pop()
            for t in self.__uAut.out(init):
                if (t.cond & event) != buddy.bddfalse and t.dst in self.__uFin:
                    uInitAux.add(t.dst)
        self.__uInit = uInitAux
        foundP = len(self.__pInit) > 0
        foundN = len(self.__nInit) > 0
        foundU = len(self.__uInit) > 0
        if not foundN and not foundU:
            return Verdict.tt
        elif not foundP and not foundU:
            return Verdict.ff
        elif not foundP and not foundN:
            return Verdict.undefined
        elif not foundN:
            return Verdict.nf
        elif not foundP:
            return Verdict.nt
        else:
            return Verdict.unknown

def explicit_ltl(ltlstr, sim):
    for lst in sim:
        for atom in lst:
            ltlstr = ltlstr.replace('!' + atom, atom + 'ff')
    for lst in sim:
        print(lst)
        for atom in lst:
            print(atom)
            j = 0
            while True:
                i = ltlstr.find(atom, j)
                if i == -1:
                    break
                if (i+len(atom)) >= len(ltlstr) or ltlstr[i+len(atom)] != 'f':
                    ltlstr = ltlstr[:i] + atom + 'tt' + ltlstr[i+len(atom):]
                j = i+1
    return ltlstr

def main(args):
    # ltl = ltl.negative_normal_form()
    ltl = 'X a'
    ap = ['a', 'b', 'c']
    mon = Monitor(ltl, ap)

if __name__ == '__main__':
    main(sys.argv)
