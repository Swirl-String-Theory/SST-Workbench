cmake_minimum_required(VERSION 3.18)
project(a053_native LANGUAGES CXX)

# Use pybind11's modern FindPython mode. run_build_cpp.cmd supplies the exact
# pybind11 CMake package directory reported by the active virtual environment.
set(PYBIND11_FINDPYTHON ON)
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(a053_native MODULE bindings.cpp)
target_compile_features(a053_native PRIVATE cxx_std_17)

# Prefer self-contained GNU/MinGW extension modules. This removes the two most
# common GCC runtime DLL dependencies; the runner also stages any remaining
# compiler runtime DLLs next to the .pyd as a defensive fallback.
if(MINGW)
  target_link_options(a053_native PRIVATE -static-libgcc -static-libstdc++)
endif()
