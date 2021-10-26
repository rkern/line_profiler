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


find_package(PythonInterp REQUIRED)


###
# Find scikit-build and include its cmake resource scripts
#
if (NOT SKBUILD)
  pycmd(skbuild_location "import os, skbuild; print(os.path.dirname(skbuild.__file__))")
  set(skbuild_cmake_dir "${skbuild_location}/resources/cmake")
  message(STATUS "[LINE_PROFILER] skbuild_cmake_dir = ${skbuild_cmake_dir}")
  # If skbuild is not the driver, then we need to include its utilities in our CMAKE_MODULE_PATH
  list(APPEND CMAKE_MODULE_PATH ${skbuild_cmake_dir})
endif()


find_package(Cython REQUIRED)
find_package(PythonExtensions REQUIRED)
find_package(PythonLibs REQUIRED)

add_subdirectory("line_profiler")
