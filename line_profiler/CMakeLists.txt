set(cython_source
  "${CMAKE_CURRENT_SOURCE_DIR}/_line_profiler.pyx"
  "${CMAKE_CURRENT_SOURCE_DIR}/python25.pxd"
)
set(module_name "_line_profiler")

# Translate Cython into C/C++
add_cython_target(${module_name} "${cython_source}" C OUTPUT_VAR sources)

# Add any other non-cython dependencies to the sources
list(APPEND sources
  "${CMAKE_CURRENT_SOURCE_DIR}/unset_trace.c"
  "${CMAKE_CURRENT_SOURCE_DIR}/timers.c"
)
message(STATUS "[OURS] sources = ${sources}")

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
#set(_install_dest ".")

#message(STATUS "_install_dest = ${_install_dest}")
#install(TARGETS ${module_name} LIBRARY DESTINATION "${_install_dest}")
file(RELATIVE_PATH _install_dest "${CMAKE_SOURCE_DIR}" "${CMAKE_CURRENT_SOURCE_DIR}")
message(STATUS "[OURS] _install_dest = ${_install_dest}")
install(TARGETS ${module_name} LIBRARY DESTINATION "${_install_dest}/")
