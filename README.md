# Animated Fibonacci Galaxy

Create a mathematically guided spiral galaxy using Python, NumPy, Matplotlib, Pillow, and FFmpeg.

The project builds a true Fibonacci square tiling, draws a connected quarter-circle spiral through the squares and distributes thousands of stars around that path. The animation begins near the center and grows outward golden spiral leads the motion while stars appear behind it, gradually forming the galaxy.

By default, the animation plays in a popup window and is not saved to disk. An optional command-line argument exports the same animation as a high-quality MP4.

![Final Fibonacci Galaxy frame](previews-v2/preview-100-final.png)

## Features

- A mathematically calculated Fibonacci sequence beginning with `1, 1`
- Ten adjoining Fibonacci squares with sides from `1` through `55`
- Connected quarter-circle arcs that form the visible Fibonacci spiral
- Approximately 8,000 procedurally generated galaxy particles
- A secondary, dimmer arm for a more natural galaxy shape
- Warm stars near the center and cooler blue or violet stars farther out
- Approximately 2,000 independent background stars
- A blurred galactic core, nebula glow, and dust texture created with Pillow
- A gold spiral with a soft outer glow
- Subtle cyan square boundaries and Fibonacci-value labels
- Smooth opacity, rotation, zoom, and particle-twinkle animation
- Reproducible artwork through a fixed random seed
- Native popup playback using Matplotlib and Tkinter
- Optional H.264 MP4 export through ImageIO-FFmpeg
- Fast smoke-test mode for checking changes without a full render
- Opening, midpoint, and final PNG preview generation
- Automated tests for the sequence, geometry, reproducibility, popup routing,
  and export routing

## Requirements

Install the required Python packages from the project directory:

```powershell
python -m pip install -r requirements.txt
```

## Quick Start

Run the project from its main directory:

```powershell
python run_galaxy.py
```

The animation opens in a popup window, plays for 12 seconds, pauses for one second, and then repeats. Close the window to stop the program.

The popup does not create an MP4 file. This is intentional. File export only happens when `--output` is supplied.

## Export an MP4

Create the full 1440 by 1440 animation:

```powershell
python run_galaxy.py --output fibonacci-galaxy.mp4
```

The default export contains 360 frames:

```text
30 frames per second × 12 seconds = 360 frames
```

The video uses H.264 compression, the widely compatible `yuv420p` pixel format, and a high-quality CRF value of `18`.

Full export can take several minutes. Do not press VS Code's Stop button, closecthe terminal, or end Python while rendering. FFmpeg must finish writing the MP4 index before the file can be opened normally.

When the export is complete, the terminal prints the output path and returns to the command prompt.

## Fast Testing

Open a lightweight popup with fewer particles, lower resolution, and a shorter duration:

```powershell
python run_galaxy.py --smoke
```

Export the lightweight version as a two-second validation video:

```powershell
python run_galaxy.py --smoke --output smoke-test.mp4
```

Smoke mode uses:

- 512 by 512 resolution
- 1,200 galaxy particles
- 350 background stars
- 12 frames per second
- Two seconds of animation

This mode is useful for confirming that the popup, animation, and FFmpeg export work before starting the full render.

## Preview Frames

Render the opening, midpoint, and final frames as PNG images:

```powershell
python run_galaxy.py --previews previews
```

The command creates:

```text
previews/
├── preview-00-opening.png
├── preview-50-midpoint.png
└── preview-100-final.png
```

Preview frames are faster to inspect than a complete video and are useful when adjusting colors, framing, labels, star density, or the spiral stroke.

## Custom Examples

### Use fewer Fibonacci terms

```powershell
python run_galaxy.py --terms 8
```

Fewer terms produce a shorter spiral and a less extreme difference between the smallest and largest squares.

### Generate a different galaxy

```powershell
python run_galaxy.py --seed 2026
```

The seed controls all procedural randomness. Running the same seed again reproduces the same star positions, colors, and sizes.

### Reduce particles for smoother popup playback

```powershell
python run_galaxy.py `
  --particles 4000 `
  --background-stars 1000
```

### Export a smaller video

```powershell
python run_galaxy.py `
  --resolution 1080 `
  --particles 5000 `
  --output fibonacci-galaxy-1080.mp4
```

### Create a longer animation

```powershell
python run_galaxy.py `
  --duration 18 `
  --fps 30 `
  --output fibonacci-galaxy-long.mp4
```

Changing the duration changes the total number of frames, but the current reveal stages still use their fixed times within the first 11 seconds. Longer durations add a longer completed hold, while durations below 11 seconds may end before every label appears.

## Command-Line Options

| Option | Purpose | Default |
| --- | --- | --- |
| `--output PATH` | Saves an MP4 instead of opening the popup | Popup only |
| `--terms N` | Number of visible Fibonacci terms and squares | `10` |
| `--seed N` | Reproducible random seed | `1618033` |
| `--particles N` | Number of galaxy-arm particles | `8000` |
| `--background-stars N` | Number of independent background stars | `2000` |
| `--fps N` | Frames per second for playback and export | `30` |
| `--duration N` | Animation duration in seconds | `12.0` |
| `--resolution N` | Width and height of the square canvas in pixels | `1440` |
| `--dpi N` | Matplotlib rendering DPI | `120` |
| `--smoke` | Uses the lightweight validation configuration | Off |
| `--previews PATH` | Creates three PNG preview frames in a directory | Off |

Run the built-in help for the current option list:

```powershell
python run_galaxy.py --help
```

## How It Works

The animation pipeline has several stages:

1. A configuration object stores the Fibonacci term count, random seed, particle counts, frame rate, duration, resolution, DPI, and output path.

2. The program generates the Fibonacci sequence beginning with `1, 1`. Zero is omitted because a square with side length zero cannot be displayed.

3. Two unit squares are placed beside each other. Every later square is added around the current bounding rectangle in the repeating order top, left, bottom, and right.

4. Each square receives an arc center and a 90-degree angle range. The endpoint of every arc matches the starting point of the following arc.

5. Each mathematical arc is sampled into a sequence of `(x, y)` coordinates so Matplotlib can draw it as a smooth line.

6. NumPy selects an arc and a position along that arc for every galaxy particle. Gaussian offsets give the arm width and prevent the stars from sitting on a perfectly thin line.

7. A portion of the particles is mirrored around the center to create a dimmer secondary arm. This adds visual realism while preserving the primaryFibonacci construction.

8. Star colors transition from warm gold near the center to cool blue farther out. A smaller violet group and a few oversized bright stars add variation.

9. Pillow draws translucent ellipses around the center and small clouds along the spiral. Gaussian blur turns those shapes into the nebula and dust layer.

10. Matplotlib assembles the background stars, nebula, galaxy particles, squares, spiral, labels, title, and golden-ratio annotation using separate drawing layers.

11. For every animation frame, the program calculates the current time, reveals more of the spiral, makes nearby stars appear behind the leading tip, adjusts their twinkle, and applies a small rotation and camera zoom.

12. The completed frames are either displayed by Tkinter in a popup window or streamed to FFmpeg and encoded as an MP4.

## The Fibonacci Geometry

The visible square sizes are:

```text
1, 1, 2, 3, 5, 8, 13, 21, 34, 55
```

Every number after the first two is calculated from the previous two:

```text
F(n) = F(n - 1) + F(n - 2)
```

Each square contains a quarter-circle whose radius equals the square's side length. Points on that circle are calculated using:

```text
x = center_x + radius × cos(angle)
y = center_y + radius × sin(angle)
```

The arc angles rotate through four ranges:

| Square placement | Start angle | End angle |
| --- | ---: | ---: |
| Top | 0° | 90° |
| Left | 90° | 180° |
| Bottom | 180° | 270° |
| Right | 270° | 360° |

The resulting Fibonacci spiral is a quarter-circle approximation of the golden spiral. Ratios between consecutive Fibonacci numbers approach the golden ratio:

```text
φ ≈ 1.618
```

## Practical Observations

During development and testing, I made several useful observations:

- A correct Fibonacci sequence does not automatically create a correct tiling.
  Every square also needs a calculated position, direction, arc center, and
  angle range.
- Arc continuity is easier to verify numerically than visually. Testing that
  one endpoint equals the next starting point catches tiny geometry mistakes.
- Placing every star directly on the mathematical curve looks artificial.
  Gaussian radial and tangent offsets preserve the spiral while giving it the
  width of a galaxy arm.
- A fixed random seed is important for creative development. Without it, every
  render changes and visual comparisons become unreliable.
- A log-normal size distribution looks more natural than equal star sizes
  because it creates many small stars and a few rare bright ones.
- Blur should be calculated once before animation whenever possible. Blurring a
  large nebula image during every frame would make rendering much slower.
- The gold line must lead the star reveal by a small amount. If both appear at
  exactly the same progress, the mathematical construction becomes harder to
  notice.
- A subtle camera movement works better than a dramatic rotation. Too much
  motion makes the Fibonacci squares and labels difficult to follow.
- Popup playback and production rendering have different performance needs.
  Smoke mode is more useful for frequent experiments, while full settings are
  intended for the finished export.
- An MP4 may exist on disk before it is valid. FFmpeg must finish and write its
  index before video players can open it.

## What I Learned

Through this project, I learned that a Fibonacci spiral illustration involves
more than repeatedly turning by 90 degrees. The squares must be positioned
around a growing bounding rectangle, and each quarter-circle needs the correct
corner and angle range to connect with the next one.

I learned how useful data classes are for grouping related mathematical values.
Storing a square's position, size, direction, arc center, and angles together
made the geometry easier to understand and reduced the chance of mixing up
individual variables.

I also learned how NumPy arrays make procedural artwork possible at a larger
scale. Instead of treating each star as a separate object, the project stores
positions, colors, sizes, progress values, and arm assignments in arrays. This
allows one calculation to update thousands of particles.

Another important lesson was the difference between randomness and
reproducibility. Random variation makes the galaxy look organic, but a fixed
seed makes the result testable and allows the same design to be rendered again.

The animation taught me to think of every visual effect as a function of time.
The spiral, particles, labels, rotation, and zoom do not need separate scripts.
Each one receives the current time and calculates how visible or transformed it
should be during that frame.

Finally, I learned why professional creative workflows use inexpensive checks
before expensive exports. Automated tests catch mathematical errors, preview
frames catch composition problems, and smoke mode catches animation or codec
problems. The full 360-frame render is only necessary after those checks pass.

## Testing

Run the regression suite from the project directory:

```powershell
python -m pytest -q
```

The suite currently contains eight tests covering:

- The expected ten-value Fibonacci sequence
- Correct square sizes and non-overlapping interiors
- Arc samples remaining inside their assigned squares
- Continuous endpoints between neighboring arcs
- Reproducible particle positions, colors, and progress values
- Popup playback being selected when no output path is supplied
- MP4 export being selected only when `--output` is supplied
- The animation remaining alive while the popup window is open

Generate preview frames after changing visual code:

```powershell
python run_galaxy.py --previews test-previews
```

Run a short export test before a full render:

```powershell
python run_galaxy.py --smoke --output test-export.mp4
```

## Troubleshooting

### The popup does not open

Confirm that Tkinter is available:

```powershell
python -m tkinter
```

A small Tk window should appear. On Windows, reinstall Python from python.org
and include Tcl/Tk support if the command fails. Headless terminals and some
remote environments cannot display desktop windows; use `--output` there.

### The popup is slow or skips frames

Use smoke mode:

```powershell
python run_galaxy.py --smoke
```

Or reduce the full configuration:

```powershell
python run_galaxy.py --particles 3500 --background-stars 800 --resolution 900
```

Popup playback depends on CPU speed. A saved MP4 may still play smoothly
because every frame is rendered before normal video playback begins.

### The MP4 is corrupt or reports `moov atom not found`

The render was interrupted before FFmpeg finalized the file. Delete or rename
the incomplete output and render it again:

```powershell
python run_galaxy.py --output new-fibonacci-galaxy.mp4
```

Wait until the output path is printed and the terminal prompt returns. Do not
stop the process because the file is visible in the folder; it is not complete
until FFmpeg exits successfully.

### The MP4 export takes too long

Test the encoder with smoke mode first:

```powershell
python run_galaxy.py --smoke --output smoke-test.mp4
```

For a faster final export, lower the resolution or particle count:

```powershell
python run_galaxy.py `
  --resolution 1080 `
  --particles 5000 `
  --output faster-galaxy.mp4
```

### `ModuleNotFoundError` appears

Install all project dependencies with the same Python interpreter used to run
the project:

```powershell
python -m pip install -r requirements.txt
```

Using `python -m pip` is safer than calling `pip` directly because VS Code may
have more than one Python installation available.

### VS Code runs the wrong Python environment

Open the Command Palette, choose **Python: Select Interpreter**, and select the
environment where the requirements were installed. Then confirm it in the
terminal:

```powershell
python --version
python -m pip show numpy matplotlib Pillow imageio-ffmpeg
```

### The output is saved in an unexpected folder

Relative paths are resolved from the terminal's current working directory. Use
an explicit path when necessary:

```powershell
python run_galaxy.py --output "C:\Videos\fibonacci-galaxy.mp4"
```

### The popup repeats after finishing

This is expected. The animation pauses for one second and then loops. Close the
popup window to stop it.

## Limitations

- The artwork is a procedural illustration rather than an astrophysical galaxy
  simulation.
- The Fibonacci spiral uses connected quarter-circles and is an approximation
  of the logarithmic golden spiral.
- Matplotlib popup performance depends on the computer's CPU and GUI backend.
- The full 1440 by 1440 render can take several minutes.
- Very high particle counts may use substantial memory and slow every frame.
- The animation has no pause, seek, speed, or restart controls inside the popup.
- The current timing is tuned for 12 seconds and is not automatically rescaled
  for extremely short custom durations.
- The project uses a square canvas and does not automatically create landscape
  or portrait compositions.
- Text placement is tuned for ten terms and may need adjustment with much larger
  sequences.
- Passing an existing path to `--output` may replace that separate output file
  without a confirmation prompt.

## Future Improvements

Ideas I would like to explore next include:

- Popup controls for pause, replay, playback speed, and frame seeking
- Sliders for Fibonacci terms, particles, colors, glow, and animation duration
- A progress indicator during MP4 rendering
- Writing exports to a temporary `.partial` file and renaming them only after
  FFmpeg finishes successfully
- Automatic detection and reporting of incomplete MP4 files
- Presets for scientific, realistic, neon, minimalist, and deep-space styles
- Landscape, portrait, and social-media aspect ratios
- Additional galaxy arms and more detailed procedural dust lanes
- Optional logarithmic golden-spiral comparison alongside the Fibonacci arcs
- Tooltips or narration explaining the sequence as each square appears
- GPU-accelerated particles for smoother real-time playback
- Optional music or generated ambient audio in exported videos
- SVG or high-resolution still-image export for posters
- A packaged desktop application that runs without opening a terminal

## Safety and Output Behavior

Popup mode does not save or overwrite files.

MP4 mode writes to the exact path supplied through `--output`. If a separate
file already exists at that path, FFmpeg may replace it. Use a new filename when
you want to preserve an earlier render.

Do not use the same path for important unrelated data. Do not interrupt an MP4
render after the output file appears; the file remains incomplete until the
terminal reports success.
