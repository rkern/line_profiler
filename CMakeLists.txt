cmake_minimum_required(VERSION 3.13.0)
project(_line_profiler LANGUAGES C)

###
# Private helper function to execute `python -c "<cmd>"`
#
# Runs a python command and populates an outvar with the result of stdout.
# Be careful of indentation if `cmd` is multiline.
#
function(pycmd outvar cmd)
  execute_process(
    COMMAND "${PYTHON_EXECUTABLE}" -c "${cmd}"
    RESULT_VARIABLE _exitcode
    OUTPUT_VARIABLE _output)
  if(NOT ${_exitcode} EQUAL 0)
    message(ERROR "Failed when running python code: \"\"\"
${cmd}\"\"\"")
    message(FATAL_ERROR "Python command failed with error code: ${_exitcode}")
  endif()
  # Remove supurflous newlines (artifacts of print)
  string(STRIP "${_output}" _output)
  set(${outvar} "${_output}" PARENT_SCOPE)
endfunction()


###
# Find scikit-build and include its cmake resource scripts
#
if (NOT SKBUILD)
  pycmd(skbuild_location "import os, skbuild; print(os.path.dirname(skbuild.__file__))")
  set(skbuild_cmake_dir "${skbuild_location}/resources/cmake")
  # If skbuild is not the driver, then we need to include its utilities in our CMAKE_MODULE_PATH
  list(APPEND CMAKE_MODULE_PATH ${skbuild_cmake_dir})
endif()


find_package(Cython REQUIRED)
find_package(PythonExtensions REQUIRED)
find_package(PythonLibs REQUIRED)
find_package(PythonInterp REQUIRED)

set(cython_source "_line_profiler.pyx" "python25.pxd")
set(module_name "_line_profiler")

# Translate Cython into C/C++
add_cython_target(${module_name} "${cython_source}" C OUTPUT_VAR sources)

# Add any other non-cython dependencies to the sources
list(APPEND sources
  "unset_trace.c"
  "timers.c"
)
message(STATUS "sources = ${sources}")

# Create C++ library. Specify include dirs and link libs as normal
add_library(${module_name} MODULE ${sources})
target_include_directories(${module_name} PUBLIC
  ${PYTHON_INCLUDE_DIRS}
  ${CMAKE_CURRENT_SOURCE_DIR}  # for the pure c files defined here
)

# Transform the C++ library into an importable python module
python_extension_module(${module_name})

# Install the C++ module to the correct relative location
# (this will be an inplace build if you use `pip install -e`)
#file(RELATIVE_PATH _install_dest "${CMAKE_SOURCE_DIR}" "${CMAKE_CURRENT_SOURCE_DIR}")
set(_install_dest ".")

message(STATUS "_install_dest = ${_install_dest}")
install(TARGETS ${module_name} LIBRARY DESTINATION "${_install_dest}")
