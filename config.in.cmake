include(CMakeFindDependencyMacro)
# Copy any dependencies here
find_dependency(Boost REQUIRED COMPONENTS log log_setup system)

include(${CMAKE_CURRENT_LIST_DIR}/@PROJECT_NAME@Targets.cmake)