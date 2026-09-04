Create an NPZ with:
  D_struct            shape (nt,...,3)
  ampere_minus_J      shape (nt,...,3)
  dt                  scalar seconds
The blind runner computes dD_struct/dt internally, fits one scalar coefficient
on preregistered training times, and evaluates closure only on held-out times.
