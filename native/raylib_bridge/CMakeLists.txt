cmake_minimum_required(VERSION 3.20)
project(somnia_raylib_bridge VERSION 0.1.0 LANGUAGES C)

find_package(raylib CONFIG REQUIRED)

add_library(somnia_raylib_bridge SHARED
    src/somnia_raylib_bridge.c
)

target_include_directories(somnia_raylib_bridge
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(somnia_raylib_bridge PRIVATE raylib)
target_compile_features(somnia_raylib_bridge PRIVATE c_std_99)

set_target_properties(somnia_raylib_bridge PROPERTIES
    C_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN YES
    OUTPUT_NAME somnia_raylib_bridge
)

install(TARGETS somnia_raylib_bridge
    RUNTIME DESTINATION native
    LIBRARY DESTINATION native
    ARCHIVE DESTINATION lib
)
install(FILES include/somnia_raylib_bridge.h DESTINATION include)
