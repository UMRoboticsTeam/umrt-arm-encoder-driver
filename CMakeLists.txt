cmake_minimum_required(VERSION 3.5)
project(arm-encoder-driver)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ********** Setup CMake **********

# Default to C++17
if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    # enables building a static library but later link it into a dynamic library
    add_compile_options(-fPIC)
endif()
if(NOT WIN32)
    # About -Wno-sign-conversion: With Clang, -Wconversion implies -Wsign-conversion. There are a number of
    # implicit sign conversions in gtest.cc, see https://ci.ros2.org/job/ci_osx/9381/clang/.
    # Hence disabling -Wsign-conversion for now until all those have eventually been fixed.
    # (from https://github.com/ros2/rcutils/pull/263#issuecomment-663252537)
    add_compile_options(-Wall -Wextra -Wconversion -Wno-sign-conversion -Wpedantic)
endif()

# Setup Boost
find_package(Boost REQUIRED COMPONENTS log log_setup thread system filesystem)
include_directories(${Boost_INCLUDE_DIRS})

# ********** Setup umrt_arm_firmware_lib library **********

set(umrt_arm_firmware_lib_sources
        src/encoder_interface.cpp
        )
set_source_files_properties(
        ${umrt_arm_firmware_lib_sources}
        PROPERTIES language "CXX")
add_library(
        ${PROJECT_NAME}
        ${umrt_arm_firmware_lib_sources})
target_include_directories(${PROJECT_NAME} PUBLIC
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include/${PROJECT_NAME}>"
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/include/${PROJECT_NAME}>"
        "$<INSTALL_INTERFACE:include/${PROJECT_NAME}>")


target_link_libraries(${PROJECT_NAME}
        ${Boost_LIBRARIES}
        )

set(public_headers
        include/arm-encoder-driver/encoder_interface.hpp
        )

set_target_properties(${PROJECT_NAME} PROPERTIES LINKER_LANGUAGE CXX)
set_target_properties(${PROJECT_NAME} PROPERTIES PUBLIC_HEADER "${public_headers}")

# ********** Setup encoder_dump executable **********

set(encoder_dump_target encoder_dump)
set(encoder_dump_sources
        src/main.cpp
        )
set_source_files_properties(
        ${encoder_dump_sources}
        PROPERTIES language "CXX")
add_executable(
        ${encoder_dump_target}
        ${encoder_dump_sources})
target_include_directories(${encoder_dump_target} PUBLIC
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}/include>"
        "$<INSTALL_INTERFACE:include/${PROJECT_NAME}>")

target_link_libraries(${encoder_dump_target}
        ${PROJECT_NAME}
        )

set_target_properties(${encoder_dump_target} PROPERTIES LINKER_LANGUAGE CXX)

# ********** Setup packaging **********

include(GNUInstallDirs)
install(TARGETS ${PROJECT_NAME}
        EXPORT "${PROJECT_NAME}Targets"
        COMPONENT ${PROJECT_NAME}
        PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/${PROJECT_NAME}
        INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
        )

install(TARGETS ${encoder_dump_target}
        EXPORT "${encoder_dump_target}Targets"
        COMPONENT ${encoder_dump_target}
        PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/${PROJECT_NAME}
        INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
        )

message(STATUS "Components to pack: ${CPACK_COMPONENTS_ALL}")
include(cpack.cmake)