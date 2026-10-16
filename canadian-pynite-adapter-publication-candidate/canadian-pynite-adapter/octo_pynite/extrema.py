"""Exact-polynomial first-order displacement extrema for pinned PyNite 3.2.0.
Uses endpoints and all real roots of each segment's quartic derivative.
"""
import numpy as np
from importlib.metadata import version

def deflection_extrema(member,axis,combo):
    if version('PyniteFEA')!='3.2.0':raise ValueError('Segment extrema implementation requires reviewed PyNite 3.2.0')
    values=[]
    for sub in member.sub_members.values():
        sub._segment_member(combo)
        segments=sub.SegmentsZ if axis=='dy' else sub.SegmentsY
        for seg in segments:
            L=seg.length();EI=seg.EI
            # dy'=theta-Mx/EI+Vx²/(2EI)+w1x³/(6EI)+(w2-w1)x⁴/(24EI L)
            # dz'=-theta+Mx/EI+Vx²/(2EI)+w1x³/(6EI)+(w2-w1)x⁴/(24EI L)
            sign=1 if axis=='dy' else -1
            coeff=[sign*seg.theta1,-sign*seg.M1/EI,seg.V1/(2*EI),seg.w1/(6*EI),(seg.w2-seg.w1)/(24*EI*L)]
            scaled=np.array([c*L**i for i,c in enumerate(coeff)])
            roots=np.polynomial.polynomial.polyroots(scaled)
            points=[0.,L]+[min(L,max(0.,float(r.real)*L)) for r in roots if abs(r.imag)<1e-8 and -1e-10<=r.real<=1+1e-10]
            values.extend(float(seg.deflection(x,False)) for x in points)
    return min(values),max(values)
