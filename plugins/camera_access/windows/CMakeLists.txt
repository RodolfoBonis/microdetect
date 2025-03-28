cmake_minimum_required(VERSION 3.14)
set(PROJECT_NAME "camera_access")
project(${PROJECT_NAME} LANGUAGES CXX)

# This value is used when generating builds using this plugin, so it must
# not be changed
set(PLUGIN_NAME "camera_access_plugin")

add_library(${PLUGIN_NAME} SHARED
  "camera_access_plugin.cpp"
  "camera_access_plugin.h"
  "camera_manager.cpp"
  "camera_manager.h"
)

apply_standard_settings(${PLUGIN_NAME})
set_target_properties(${PLUGIN_NAME} PROPERTIES CXX_VISIBILITY_PRESET hidden)
target_compile_definitions(${PLUGIN_NAME} PRIVATE FLUTTER_PLUGIN_IMPL)
target_include_directories(${PLUGIN_NAME} INTERFACE
  "${CMAKE_CURRENT_SOURCE_DIR}/include")
target_link_libraries(${PLUGIN_NAME} PRIVATE flutter flutter_wrapper_plugin)

# Sistema Media Foundation para câmeras
target_link_libraries(${PLUGIN_NAME} PRIVATE mfplat mf mfreadwrite mfuuid)

# List of absolute paths to libraries that should be bundled with the plugin
set(camera_access_bundled_libraries
  ""
  PARENT_SCOPE
)