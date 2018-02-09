gource \
    -f \
    -s .06 \
    -1920x1080 \
    --auto-skip-seconds .1 \
    --multi-sampling \
    --stop-at-end \
    --key \
    --highlight-users \
    --hide mouse,progress \
    --file-idle-time 0 \
    --max-files 0 \
    --background-colour 000000 \
    --font-size 22 \
    --title "My title" \
    --output-ppm-stream - \
    --output-framerate 60 \
    | ffmpeg -y \
    -framerate 60 \
    -f image2pipe \
    -vcodec ppm \
    -i - \
    -b:v 65536K \
    -me_method full \
    gource.mp4
