cmake_minimum_required(VERSION 3.9)
project(method)

set(CMAKE_INSTALL_SO_NO_EXE 1)

find_package (Eigen3 3.3 REQUIRED NO_MODULE)

include_directories(${{CHARGEFW2_DIR}}/include)
link_directories(${{CHARGEFW2_DIR}}/lib)


set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}} -march=native -O3 -s")

add_library(method SHARED ccl_method.h ccl_method.cpp)
set_target_properties(method PROPERTIES OUTPUT_NAME {method_name})
target_link_libraries(method chargefw2 Eigen3::Eigen)
install(TARGETS method DESTINATION ${{CHARGEFW2_DIR}}/lib)
