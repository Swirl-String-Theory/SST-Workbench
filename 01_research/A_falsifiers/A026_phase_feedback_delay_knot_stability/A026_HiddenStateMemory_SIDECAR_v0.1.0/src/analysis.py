"""Predeclared independent-trial train/test prediction comparison."""
import numpy as np


def _fit_predict(features, target, train, test):
    X0=np.asarray(features,dtype=float)
    if not np.all(np.isfinite(X0)): raise ValueError('nonfinite features')
    means=X0[train].mean(0)
    stds=X0[train].std(0)
    if np.any(stds < 1e-14): raise ValueError('degenerate observed feature')
    X=(X0-means)/stds
    A=np.column_stack((np.ones(len(train)),X[train]))
    B=np.column_stack((np.ones(len(test)),X[test]))
    coef=np.linalg.lstsq(A,target[train],rcond=None)[0]
    return B@coef


def compare(dataset, seed=20261029, test_fraction=0.30, bootstrap=400):
    current=np.asarray(dataset['current']); hist=np.asarray(dataset['history']); y=np.asarray(dataset['target'])
    n=len(y)
    if n < 80: raise ValueError('at least 80 independent trials required for diagnostic')
    if current.shape != (n,2) or hist.shape != (n,2): raise ValueError('current/history must have shape (n, 2)')
    if not np.all(np.isfinite(y)): raise ValueError('nonfinite targets')
    rng=np.random.default_rng(seed); ids=rng.permutation(n)
    tcount=int(round(n*test_fraction)); test=ids[:tcount]; train=ids[tcount:]
    simple=_fit_predict(current,y,train,test)
    memory=_fit_predict(np.column_stack((current,hist)),y,train,test)
    s=(y[test]-simple)**2
    m=(y[test]-memory)**2
    rmse0=float(np.sqrt(np.mean(s))); rmse1=float(np.sqrt(np.mean(m)))
    improvement=1-rmse1/rmse0 if rmse0>0 else float('nan')
    idx=rng.integers(0,len(test),size=(bootstrap,len(test)))
    b0=np.sqrt(np.mean(s[idx],axis=1)); b1=np.sqrt(np.mean(m[idx],axis=1))
    gains=1-b1/b0
    ci=[float(x) for x in np.quantile(gains,[0.025,0.975])]
    result={'n_train':len(train),'n_test':len(test),'rmse_current_m':rmse0,'rmse_history_m':rmse1,
        'relative_rmse_gain':float(improvement),'ci95_gain':ci,
        'diagnostic_history_signal':bool(ci[0]>0.05),'holdout_group':'independent_trajectories',
        'bootstrap_unit':'independent_trajectories', 'seed':seed}
    if 'full' in dataset:
        full=np.asarray(dataset['full']); p=_fit_predict(full,y,train,test)
        result['rmse_full_state_oracle_m']=float(np.sqrt(np.mean((y[test]-p)**2)))
    return result
