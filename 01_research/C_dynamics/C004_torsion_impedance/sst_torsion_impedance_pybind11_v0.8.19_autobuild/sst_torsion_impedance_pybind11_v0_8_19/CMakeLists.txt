cmake_minimum_required(VERSION 3.18)
project(sst_torsion_impedance LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(BUILD_PYBIND11_MODULE "Build pybind11 Python extension" ON)

if(BUILD_PYBIND11_MODULE)
  find_package(pybind11 REQUIRED)
  pybind11_add_module(sst_torsion_impedance src/sst_torsion_impedance.cpp)
  target_compile_definitions(sst_torsion_impedance PRIVATE BUILD_PYBIND11_MODULE)
else()
  add_executable(impedance_cli src/sst_torsion_impedance.cpp)
endif()
