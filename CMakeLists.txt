cmake_minimum_required(VERSION 3.5)
project(cpp_arm_encoder_driver)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(${PROJECT_NAME} src/encoder_interface.cpp src/main.cpp)

find_package(Boost REQUIRED COMPONENTS log log_setup thread system filesystem)
target_link_libraries(${PROJECT_NAME} Boost::log Boost::log_setup Boost::thread Boost::system Boost::filesystem pthread)
target_link_directories(${PROJECT_NAME} PUBLIC ${Boost_LIBRARIES})
target_include_directories(${PROJECT_NAME} PUBLIC ${Boost_INCLUDE_DIRS})


install(TARGETS ${PROJECT_NAME} DESTINATION lib)
