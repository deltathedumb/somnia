#define SOMNIA_RAYLIB_BRIDGE_BUILD
#include "somnia_raylib_bridge.h"

#include <raylib.h>

static unsigned char somnia_color_channel(int value)
{
    if (value < 0) {
        return 0;
    }
    if (value > 255) {
        return 255;
    }
    return (unsigned char)value;
}

static Color somnia_color(int red, int green, int blue, int alpha)
{
    Color color = {
        somnia_color_channel(red),
        somnia_color_channel(green),
        somnia_color_channel(blue),
        somnia_color_channel(alpha),
    };
    return color;
}

int somnia_raylib_open(int width, int height, const char *title)
{
    if (width <= 0 || height <= 0 || title == 0) {
        return 0;
    }
    InitWindow(width, height, title);
    return IsWindowReady() ? 1 : 0;
}

void somnia_raylib_set_target_fps(int fps)
{
    if (fps > 0) {
        SetTargetFPS(fps);
    }
}

int somnia_raylib_should_close(void)
{
    return WindowShouldClose() ? 1 : 0;
}

float somnia_raylib_frame_time(void)
{
    return GetFrameTime();
}

void somnia_raylib_begin_frame(int red, int green, int blue, int alpha)
{
    BeginDrawing();
    ClearBackground(somnia_color(red, green, blue, alpha));
}

void somnia_raylib_begin_3d(
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
)
{
    Camera3D camera = {0};
    camera.position = (Vector3){position_x, position_y, position_z};
    camera.target = (Vector3){target_x, target_y, target_z};
    camera.up = (Vector3){up_x, up_y, up_z};
    camera.fovy = field_of_view;
    camera.projection = projection == 1 ? CAMERA_ORTHOGRAPHIC : CAMERA_PERSPECTIVE;
    BeginMode3D(camera);
}

void somnia_raylib_end_3d(void)
{
    EndMode3D();
}

void somnia_raylib_end_frame(void)
{
    EndDrawing();
}

void somnia_raylib_draw_grid(int slices, float spacing)
{
    DrawGrid(slices, spacing);
}

void somnia_raylib_draw_cube(
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
)
{
    DrawCubeV(
        (Vector3){position_x, position_y, position_z},
        (Vector3){size_x, size_y, size_z},
        somnia_color(red, green, blue, alpha)
    );
}

void somnia_raylib_draw_cube_wires(
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
)
{
    DrawCubeWiresV(
        (Vector3){position_x, position_y, position_z},
        (Vector3){size_x, size_y, size_z},
        somnia_color(red, green, blue, alpha)
    );
}

void somnia_raylib_close(void)
{
    if (IsWindowReady()) {
        CloseWindow();
    }
}
