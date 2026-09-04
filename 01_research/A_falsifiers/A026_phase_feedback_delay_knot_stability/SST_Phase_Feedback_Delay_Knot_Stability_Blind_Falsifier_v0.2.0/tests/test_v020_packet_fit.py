import numpy as np
from sst_phase_delay_falsifier.packet import fit_circular_transport
def test_packet_transport_fit_recovers_velocity():
 t=np.linspace(0,2,30); slope=1.7; phase=(0.3+slope*t+np.pi)%(2*np.pi)-np.pi
 q=fit_circular_transport(t,phase,10.0,0.0)
 assert q['r2']>0.999999
 assert abs(q['v_group']-10*slope/(2*np.pi))<1e-10
