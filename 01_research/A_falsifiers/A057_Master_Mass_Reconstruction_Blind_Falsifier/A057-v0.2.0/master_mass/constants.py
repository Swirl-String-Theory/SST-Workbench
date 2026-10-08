from dataclasses import dataclass
import math

@dataclass(frozen=True)
class SSTConstants:
    v_swirl: float = 1.09384563e6
    r_c: float = 1.40897017e-15
    rho_core: float = 3.8934358266918687e18
    rho_f: float = 7.0e-7
    c: float = 299792458.0
    @property
    def circulation(self) -> float:
        return 2.0*math.pi*self.r_c*self.v_swirl
    @property
    def rho_E_background(self) -> float:
        return 0.5*self.rho_f*self.v_swirl**2
    @property
    def rho_m_background(self) -> float:
        return self.rho_E_background/self.c**2
    def line_mass_scale(self, density: float) -> float:
        return density*self.circulation**2*self.r_c/(8.0*math.pi*self.c**2)
    def tube_mass_scale(self, density: float) -> float:
        return density*self.circulation**2*self.r_c/(32.0*math.pi**2*self.c**2)
    @property
    def clock_impedance(self) -> float:
        beta2=(self.v_swirl/self.c)**2
        return 1.0/(1.0-beta2)
SST=SSTConstants()
