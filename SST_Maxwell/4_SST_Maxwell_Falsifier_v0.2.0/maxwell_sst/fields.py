from __future__ import annotations
import numpy as np
from .kernels import biot_savart_points


def swirl_gaussian_velocity(x, omega0=2.0, L=1.0):
    x=np.atleast_2d(np.asarray(x,float)); s=x[:,0]**2+x[:,1]**2
    f=0.5*omega0*np.exp(-s/L**2)
    return np.column_stack([-x[:,1]*f, x[:,0]*f, np.zeros(len(x))])


def swirl_gaussian_vorticity(x, omega0=2.0, L=1.0):
    x=np.atleast_2d(np.asarray(x,float)); s=x[:,0]**2+x[:,1]**2
    wz=omega0*np.exp(-s/L**2)*(1.0-s/L**2)
    return np.column_stack([np.zeros(len(x)),np.zeros(len(x)),wz])


def shear_velocity(x, a=0.7):
    x=np.atleast_2d(np.asarray(x,float)); return np.column_stack([a*x[:,1]**2,np.zeros(len(x)),np.zeros(len(x))])


def shear_vorticity(x, a=0.7):
    x=np.atleast_2d(np.asarray(x,float)); return np.column_stack([np.zeros(len(x)),np.zeros(len(x)),-2*a*x[:,1]])


def abc_velocity(x):
    x=np.atleast_2d(np.asarray(x,float)); X,Y,Z=x[:,0],x[:,1],x[:,2]
    return np.column_stack([np.sin(Z)+np.cos(Y),np.sin(X)+np.cos(Z),np.sin(Y)+np.cos(X)])


def finite_gradient_vector(field_fn, pts, h):
    pts=np.atleast_2d(np.asarray(pts,float)); n=len(pts); J=np.zeros((n,3,3))
    for j in range(3):
        e=np.zeros(3); e[j]=h
        fp=field_fn(pts+e); fm=field_fn(pts-e)
        J[:,:,j]=(fp-fm)/(2*h)
    return J


def div_curl(field_fn, pts, h):
    J=finite_gradient_vector(field_fn,pts,h)
    div=J[:,0,0]+J[:,1,1]+J[:,2,2]
    curl=np.column_stack([J[:,2,1]-J[:,1,2], J[:,0,2]-J[:,2,0], J[:,1,0]-J[:,0,1]])
    return div,curl


def grad_speed2(field_fn, pts, h):
    pts=np.atleast_2d(np.asarray(pts,float)); g=np.zeros_like(pts)
    for j in range(3):
        e=np.zeros(3); e[j]=h
        vp=field_fn(pts+e); vm=field_fn(pts-e)
        sp=np.einsum('ij,ij->i',vp,vp); sm=np.einsum('ij,ij->i',vm,vm)
        g[:,j]=(sp-sm)/(2*h)
    return g
