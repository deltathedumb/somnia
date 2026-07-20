#ifndef SOMNIA_RAYLIB_BRIDGE_H
#define SOMNIA_RAYLIB_BRIDGE_H

#ifdef _WIN32
#  ifdef SOMNIA_RAYLIB_BRIDGE_BUILD
#    define SOMNIA_RAYLIB_API __declspec(dllexport)
#  else
#    define SOMNIA_RAYLIB_API __declspec(dllimport)
#  endif
#else
#  define SOMNIA_RAYLIB_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

SOMNIA_RAYLIB_API int somnia_raylib_open(
    int width,
    int height,
    const char *title
);
SOMNIA_RAYLIB_API void somnia_raylib_set_target_fps(int fps);
SOMNIA_RAYLIB_API int somnia_raylib_should_close(void);
SOMNIA_RAYLIB_API float somnia_raylib_frame_time(void);

SOMNIA_RAYLIB_API void somnia_raylib_begin_frame(
    int red,
    int green,
    int blue,
    int alpha
);
SOMNIA_RAYLIB_API void somnia_raylib_begin_3d(
    float position_x,
    float position_y,
    float position_z,
    float target_x,
    float target_y,
    float target_z,
    float up_x,
    float up_y,
    float up_z,
    float field_of_view,
    int projection
);
SOMNIA_RAYLIB_API void somnia_raylib_end_3d(void);
SOMNIA_RAYLIB_API void somnia_raylib_end_frame(void);

SOMNIA_RAYLIB_API void somnia_raylib_draw_grid(int slices, float spacing);
SOMNIA_RAYLIB_API void somnia_raylib_draw_cube(
    float position_x,
    float position_y,
    float position_z,
    float size_x,
    float size_y,
    float size_z,
    int red,
    int green,
    int blue,
    int alpha
);
SOMNIA_RAYLIB_API void somnia_raylib_draw_cube_wires(
    float position_x,
    float position_y,
    float position_z,
    float size_x,
    float size_y,
    float size_z,
    int red,
    int green,
    int blue,
    int alpha
);

SOMNIA_RAYLIB_API void somnia_raylib_close(void);

#ifdef __cplusplus
}
#endif

#endif
