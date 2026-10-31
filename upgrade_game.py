from pathlib import Path

root = Path('farm_market_android')
if not root.is_dir():
    root = Path('.')
p = root / 'app/src/main/cpp/main.cpp'
s = p.read_text(encoding='utf-8')

def replace_once(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected one match, found {n}')
    s = s.replace(old, new, 1)

replace_once('''struct TouchControls {
    float forward = 0.0f;
    float strafe = 0.0f;
    bool action = false;''', '''struct TouchControls {
    float forward = 0.0f;
    float strafe = 0.0f;
    bool joystickActive = false;
    float joystickOriginX = 165.0f;
    float joystickOriginY = 750.0f;
    float joystickKnobX = 165.0f;
    float joystickKnobY = 750.0f;
    bool action = false;''', 'touch struct')

start = s.index('TouchControls ReadTouchControls() {')
end = s.index('\nvoid DrawTouchButton(', start)
new_read = r'''TouchControls ReadTouchControls() {
    static int joystickTouchId = -1;
    static Vector2 joystickOrigin = {165.0f, 750.0f};
    static bool actionWasDown = false, waterWasDown = false, buyWasDown = false;
    static bool upgradeWasDown = false, saveWasDown = false, loadWasDown = false;
    static bool helpWasDown = false, pauseWasDown = false;

    TouchControls result{};
    const int count = std::min(GetTouchPointCount(), 8);
    bool joystickFound = false;
    for (int i = 0; i < count; ++i) {
        const Vector2 p = ScreenToUi(GetTouchPosition(i));
        const int id = GetTouchPointId(i);
        if (id == joystickTouchId) {
            joystickFound = true;
        } else if (joystickTouchId < 0 && p.x >= 36.0f && p.x <= 285.0f &&
                   p.y >= 595.0f && p.y <= 890.0f) {
            joystickTouchId = id;
            joystickOrigin = p;
            joystickFound = true;
        }
        if (id == joystickTouchId && joystickTouchId >= 0) {
            joystickFound = true;
            float dx = (p.x - joystickOrigin.x) / 82.0f;
            float dy = (p.y - joystickOrigin.y) / 82.0f;
            const float length = std::sqrt(dx*dx + dy*dy);
            if (length > 1.0f) { dx /= length; dy /= length; }
            if (length < 0.12f) { dx = 0.0f; dy = 0.0f; }
            result.strafe = dx;
            result.forward = -dy;
            result.joystickActive = true;
            result.joystickOriginX = joystickOrigin.x;
            result.joystickOriginY = joystickOrigin.y;
            result.joystickKnobX = joystickOrigin.x + dx * 82.0f;
            result.joystickKnobY = joystickOrigin.y + dy * 82.0f;
        }
    }
    if (!joystickFound) joystickTouchId = -1;

    result.action = TouchPressed({1240, 670, 170, 170}, actionWasDown);
    result.water = TouchPressed({1085, 770, 130, 110}, waterWasDown);
    result.buy = TouchPressed({1040, 555, 150, 82}, buyWasDown);
    result.upgrade = TouchPressed({1205, 555, 190, 82}, upgradeWasDown);
    result.save = TouchPressed({300, 780, 88, 76}, saveWasDown);
    result.load = TouchPressed({395, 780, 88, 76}, loadWasDown);
    result.help = TouchPressed({1320, 210, 82, 58}, helpWasDown);
    result.pause = TouchPressed({1230, 210, 82, 58}, pauseWasDown);
    result.rotateLeftDown = AnyTouchIn({890, 770, 86, 86});
    result.rotateRightDown = AnyTouchIn({980, 770, 86, 86});
    return result;
}
'''
s = s[:start] + new_read + s[end:]

replace_once('''void DrawTouchControls(bool nearField, bool nearMarket) {
    // Left thumb movement pad.
    DrawCircle(165, 750, 105, Fade({27, 42, 45, 255}, 0.34f));
    DrawCircleLines(165, 750, 105, Fade({245, 244, 217, 255}, 0.50f));
    DrawCircle(165, 750, 37, Fade({228, 235, 218, 255}, 0.38f));
    DrawText("MOVE", 132, 744, 15, Fade(WHITE, 0.88f));''', '''void DrawTouchControls(bool nearField, bool nearMarket, const TouchControls& touch) {
    const float jx = touch.joystickActive ? touch.joystickOriginX : 165.0f;
    const float jy = touch.joystickActive ? touch.joystickOriginY : 750.0f;
    const float kx = touch.joystickActive ? touch.joystickKnobX : jx;
    const float ky = touch.joystickActive ? touch.joystickKnobY : jy;
    DrawCircle(static_cast<int>(jx), static_cast<int>(jy), 96, Fade({27, 42, 45, 255}, 0.34f));
    DrawCircleLines(static_cast<int>(jx), static_cast<int>(jy), 96, Fade({245, 244, 217, 255}, 0.64f));
    DrawCircle(static_cast<int>(kx), static_cast<int>(ky), 43, Fade({228, 235, 218, 255}, 0.78f));
    DrawCircleLines(static_cast<int>(kx), static_cast<int>(ky), 43, Fade(WHITE, 0.85f));
    DrawText("MOVE", static_cast<int>(jx) - 32, static_cast<int>(jy) - 8, 16, Fade(WHITE, 0.96f));''', 'touch visual')
replace_once('''        DrawTouchControls(nearField, nearMarket);''', '''        DrawTouchControls(nearField, nearMarket, touch);''', 'touch call')

music_fn = r'''
Sound CreateFarmMusic() {
    // Original, mellow plucked-string and bell loop generated locally: no network or assets.
    constexpr int sampleRate = 22050, stepCount = 32;
    constexpr float stepSeconds = 0.38f;
    constexpr int frameCount = static_cast<int>(sampleRate * stepCount * stepSeconds);
    short* pcm = static_cast<short*>(MemAlloc(frameCount * sizeof(short)));
    if (!pcm) return {0};
    const int melody[] = {0,4,7,12,7,4,2,4, 5,9,12,17,12,9,7,9,
                          3,7,10,15,10,7,5,7, 4,7,11,16,11,7,4,2};
    const int roots[] = {0,5,3,4};
    const float twoPi = 6.28318530718f;
    for (int i = 0; i < frameCount; ++i) {
        const float t = static_cast<float>(i) / sampleRate;
        const int step = std::min(stepCount - 1, static_cast<int>(t / stepSeconds));
        const int bar = step / 8;
        const float age = t - step * stepSeconds;
        const float semitone = static_cast<float>(melody[step] + roots[bar] + 12);
        const float noteHz = 261.6256f * std::pow(2.0f, semitone / 12.0f);
        const float env = std::exp(-age * 5.2f);
        const float pluck = (std::sin(twoPi * noteHz * age) +
            0.22f * std::sin(twoPi * noteHz * 2.01f * age)) * env * 0.20f;
        const float bassHz = 65.4064f * std::pow(2.0f, static_cast<float>(roots[bar]) / 12.0f);
        const float bass = std::sin(twoPi * bassHz * t) * 0.055f +
            std::sin(twoPi * bassHz * 1.5f * t) * 0.018f;
        const float padHz = 130.8128f * std::pow(2.0f, static_cast<float>(roots[bar] + 7) / 12.0f);
        const float pad = std::sin(twoPi * padHz * t) * 0.025f;
        const float fadeIn = std::min(1.0f, t / 0.08f);
        const float fadeOut = std::min(1.0f, (stepCount * stepSeconds - t) / 0.08f);
        const float sample = Clamp((pluck + bass + pad) * fadeIn * fadeOut, -0.85f, 0.85f);
        pcm[i] = static_cast<short>(sample * 32767.0f);
    }
    Wave wave{};
    wave.frameCount = frameCount;
    wave.sampleRate = sampleRate;
    wave.sampleSize = 16;
    wave.channels = 1;
    wave.data = pcm;
    Sound sound = LoadSoundFromWave(wave);
    MemFree(pcm);
    return sound;
}

'''
replace_once('''void DrawWorld(float time, const std::array<CropField, 3>& fields,''',
             music_fn + '''void DrawWorld(float time, const std::array<CropField, 3>& fields,''', 'music')

village_fn = r'''
void DrawVillageHouse(float x, float z, float width, float depth,
                      Color wall, Color roof, float windowGlow) {
    const float eave = 2.30f, ridge = 3.35f;
    const float halfW = width * 0.5f, halfD = depth * 0.5f;
    const float frontZ = z + halfD, backZ = z - halfD;
    const Vector3 fl = V3(x-halfW,eave,frontZ), fr = V3(x+halfW,eave,frontZ);
    const Vector3 bl = V3(x-halfW,eave,backZ), br = V3(x+halfW,eave,backZ);
    const Vector3 rf = V3(x,ridge,frontZ), rb = V3(x,ridge,backZ);
    DrawCubeV(V3(x,1.13f,z), V3(width,2.26f,depth), wall);
    DrawCubeV(V3(x,0.12f,z), V3(width+0.24f,0.22f,depth+0.24f), {177,164,139,255});
    DrawTriangle3D(fl,fr,rf,wall);
    DrawTriangle3D(br,bl,rb,wall);
    DrawTriangle3D(fl,bl,rb,roof); DrawTriangle3D(fl,rb,rf,roof);
    DrawTriangle3D(fr,rf,rb,roof); DrawTriangle3D(fr,rb,br,roof);
    DrawCylinderEx(V3(x-halfW-0.10f,eave,frontZ+0.04f),
                   V3(x+halfW+0.10f,eave,frontZ+0.04f),0.075f,0.075f,8,{104,64,49,255});
    DrawCubeV(V3(x,0.83f,frontZ+0.055f),V3(0.72f,1.58f,0.10f),{104,67,48,255});
    DrawCubeV(V3(x,1.60f,frontZ+0.12f),V3(0.12f,0.12f,0.04f),{242,210,144,255});
    DrawCubeV(V3(x,0.10f,frontZ+0.30f),V3(1.05f,0.18f,0.55f),{191,174,147,255});
    for (int side : {-1,1}) {
        const float wx = x + side * width * 0.31f;
        DrawCubeV(V3(wx,1.45f,frontZ+0.075f),V3(0.62f,0.65f,0.08f),{107,76,54,255});
        DrawCubeV(V3(wx,1.45f,frontZ+0.13f),V3(0.47f,0.50f,0.035f),
                  WithAlpha({255,219,153,255},static_cast<unsigned char>(windowGlow)));
        DrawCubeV(V3(wx,1.45f,frontZ+0.16f),V3(0.045f,0.53f,0.025f),{126,89,58,255});
        DrawCubeV(V3(wx,1.45f,frontZ+0.17f),V3(0.51f,0.04f,0.025f),{126,89,58,255});
    }
    DrawCubeV(V3(x+width*0.28f,2.90f,z-depth*0.18f),V3(0.35f,1.0f,0.40f),{153,91,68,255});
    DrawCubeV(V3(x,1.01f,frontZ+0.19f),V3(1.22f,0.18f,0.20f),{118,77,48,255});
    DrawFlowerPot(V3(x-0.36f,0,frontZ+0.45f),0.36f,windowGlow*0.01f);
    DrawFlowerPot(V3(x+0.36f,0,frontZ+0.45f),0.36f,windowGlow*0.01f+1.0f);
}

void DrawVillage(float time) {
    DrawPlane(V3(0,-0.055f,-19.0f),{48.0f,19.0f},{121,169,111,255});
    DrawCubeV(V3(0,0.025f,-14.05f),V3(44.0f,0.11f,2.65f),{79,86,83,255});
    DrawCubeV(V3(0,0.085f,-15.40f),V3(44.0f,0.20f,0.32f),{199,185,155,255});
    DrawCubeV(V3(0,0.085f,-12.70f),V3(44.0f,0.20f,0.32f),{199,185,155,255});
    for (int i=0;i<11;++i) {
        const float x=-20.0f+i*4.0f;
        DrawCubeV(V3(x,0.092f,-14.05f),V3(1.7f,0.025f,0.10f),{232,220,182,255});
    }
    DrawVillageHouse(-15.5f,-21.4f,3.6f,3.1f,{225,185,146,255},{154,75,58,255},215);
    DrawVillageHouse(-9.3f,-23.0f,4.0f,3.3f,{204,218,187,255},{138,73,56,255},225);
    DrawVillageHouse(-3.2f,-21.8f,3.7f,3.0f,{224,203,157,255},{88,111,105,255},230);
    DrawVillageHouse(4.0f,-22.8f,4.1f,3.4f,{218,174,165,255},{154,81,62,255},210);
    DrawVillageHouse(10.4f,-21.5f,3.8f,3.2f,{205,216,220,255},{104,113,143,255},230);
    DrawVillageHouse(16.2f,-23.0f,3.3f,3.0f,{231,214,175,255},{154,92,56,255},220);

    DrawCubeV(V3(0.4f,3.05f,-22.5f),V3(1.7f,5.9f,1.7f),{213,199,166,255});
    DrawCubeV(V3(0.4f,6.12f,-22.5f),V3(2.0f,0.22f,2.0f),{154,84,63,255});
    DrawTriangle3D(V3(-0.65f,6.24f,-23.45f),V3(1.45f,6.24f,-23.45f),
                   V3(0.4f,7.7f,-22.5f),{135,70,55,255});
    DrawTriangle3D(V3(1.45f,6.24f,-21.55f),V3(-0.65f,6.24f,-21.55f),
                   V3(0.4f,7.7f,-22.5f),{135,70,55,255});
    DrawCubeV(V3(0.4f,4.05f,-21.62f),V3(0.95f,0.95f,0.04f),{238,226,188,255});
    DrawCircle3D(V3(0.4f,4.05f,-21.58f),0.34f,V3(1,0,0),90.0f,{74,82,75,255});

    for (int i=0;i<7;++i) {
        const float x=-18.0f+i*6.0f;
        DrawTree(V3(x,0,-17.1f),0.68f+(i%3)*0.08f,time+i,i%2==0);
        DrawCubeV(V3(x+2.25f,1.8f,-15.1f),V3(0.10f,3.5f,0.10f),{67,75,70,255});
        DrawCubeV(V3(x+2.25f,3.45f,-15.1f),V3(0.58f,0.15f,0.58f),{83,88,77,255});
        DrawSphere(V3(x+2.25f,3.27f,-15.1f),0.20f,WithAlpha({255,225,156,255},190));
    }
    DrawPerson(V3(-5.8f+std::sin(time*0.18f)*1.2f,0,-14.0f),1.57f,
               {181,103,102,255},{71,78,106,255},false,time*1.5f);
    DrawPerson(V3(7.4f+std::sin(time*0.15f+2.0f)*1.1f,0,-14.3f),-1.57f,
               {82,132,171,255},{92,91,74,255},false,time*1.3f+1.0f);
}

'''
replace_once('''void DrawWorld(float time, const std::array<CropField, 3>& fields,''',
             village_fn + '''void DrawWorld(float time, const std::array<CropField, 3>& fields,''', 'village')
replace_once('''    DrawPlane(V3(0, 0, 0), {29.0f, 27.0f}, {112, 171, 91, 255});''',
             '''    DrawPlane(V3(0, 0, 0), {29.0f, 27.0f}, {112, 171, 91, 255});
    DrawVillage(time);''', 'village call')

replace_once('''constexpr float PLAYER_SPEED = 5.2f;''', '''constexpr float PLAYER_SPEED = 7.4f;''', 'player speed')
replace_once('''    float playerYaw = 0.0f;
    float playerPhase = 0.0f;''', '''    float playerYaw = 0.0f;
    float playerPhase = 0.0f;
    Vector3 playerVelocity = V3(0.0f, 0.0f, 0.0f);''', 'player velocity')
replace_once('''    float cameraDistance = 17.0f;''', '''    float cameraDistance = 14.2f;''', 'camera distance')

old_move = '''            Vector3 move = V3(-std::sin(cameraYaw) * forward + std::cos(cameraYaw) * strafe,
                              0.0f,
                              -std::cos(cameraYaw) * forward - std::sin(cameraYaw) * strafe);
            const float moveLen = std::sqrt(move.x * move.x + move.z * move.z);
            if (moveLen > 0.001f) {
                move.x /= moveLen;
                move.z /= moveLen;
                player.x += move.x * PLAYER_SPEED * dt;
                player.z += move.z * PLAYER_SPEED * dt;
                playerYaw = std::atan2(move.x, move.z);
                playerPhase += dt * 7.0f;
            }
            player.x = Clamp(player.x, -11.6f, 11.6f);
            player.z = Clamp(player.z, -10.5f, 10.5f);'''
new_move = '''            Vector3 move = V3(-std::sin(cameraYaw) * forward + std::cos(cameraYaw) * strafe,
                              0.0f,
                              -std::cos(cameraYaw) * forward - std::sin(cameraYaw) * strafe);
            const float moveLen = std::sqrt(move.x * move.x + move.z * move.z);
            if (moveLen > 1.0f) { move.x /= moveLen; move.z /= moveLen; }
            const float inputMagnitude = std::min(1.0f, moveLen);
            const float runBoost = inputMagnitude > 0.82f ? 1.28f : 1.0f;
            const float desiredX = move.x * PLAYER_SPEED * runBoost;
            const float desiredZ = move.z * PLAYER_SPEED * runBoost;
            const float response = 1.0f - std::exp(-13.0f * dt);
            playerVelocity.x += (desiredX - playerVelocity.x) * response;
            playerVelocity.z += (desiredZ - playerVelocity.z) * response;
            player.x += playerVelocity.x * dt;
            player.z += playerVelocity.z * dt;
            const float actualSpeed = std::sqrt(playerVelocity.x * playerVelocity.x +
                                                playerVelocity.z * playerVelocity.z);
            if (actualSpeed > 0.28f) {
                playerYaw = std::atan2(playerVelocity.x, playerVelocity.z);
                playerPhase += dt * (actualSpeed / PLAYER_SPEED) * 7.0f;
            }
            player.x = Clamp(player.x, -11.6f, 11.6f);
            player.z = Clamp(player.z, -10.5f, 10.5f);
            if (player.x <= -11.59f || player.x >= 11.59f) playerVelocity.x = 0.0f;
            if (player.z <= -10.49f || player.z >= 10.49f) playerVelocity.z = 0.0f;'''
replace_once(old_move, new_move, 'movement block')
replace_once('''            if (IsKeyDown(KEY_Q) || touch.rotateLeftDown) cameraYaw -= 1.25f * dt;
            if (IsKeyDown(KEY_R) || touch.rotateRightDown) cameraYaw += 1.25f * dt;''',
             '''            if (IsKeyDown(KEY_Q) || touch.rotateLeftDown) cameraYaw -= 1.65f * dt;
            if (IsKeyDown(KEY_R) || touch.rotateRightDown) cameraYaw += 1.65f * dt;''', 'camera speed')

replace_once('''    SetTargetFPS(60);

    // Enable a soft warm key light,''', '''    SetTargetFPS(60);

    bool audioReady = false;
    Sound farmMusic = {0};
    if (!IsAudioDeviceReady()) InitAudioDevice();
    if (IsAudioDeviceReady()) {
        farmMusic = CreateFarmMusic();
        audioReady = farmMusic.frameCount > 0;
        if (audioReady) SetSoundVolume(farmMusic, 0.24f);
    }

    // Enable a soft warm key light,''', 'audio init')
replace_once('''        const TouchControls touch = ReadTouchControls();

        if (IsKeyPressed(KEY_H)''',
             
             '''        const TouchControls touch = ReadTouchControls();
        if (audioReady && !IsSoundPlaying(farmMusic)) PlaySound(farmMusic);

        if (IsKeyPressed(KEY_H)''', 'audio playback')
replace_once('''    if (lightingReady) UnloadShader(farmLighting);
    CloseWindow();''', '''    if (audioReady) UnloadSound(farmMusic);
    if (IsAudioDeviceReady()) CloseAudioDevice();
    if (lightingReady) UnloadShader(farmLighting);
    CloseWindow();''', 'audio cleanup')
replace_once('''    DrawText("LITTLE FARM MARKET 3D", 58, 39, 21, RAYWHITE);''',
             '''    DrawText("LITTLE FARM MARKET 3D", 58, 39, 21, RAYWHITE);
    DrawText("MUSIC ON", 252, 58, 10, {192, 224, 177, 255});''', 'music hud')

p.write_text(s, encoding='utf-8')
print('Applied movement, village and offline music upgrade to', p)

