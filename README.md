# Santa's Countdown

**Version 1.0.0** (2026-11-08) · by [BigC07](https://github.com/BigC07) · [Changelog](CHANGELOG.md)

An animated countdown to Christmas for [LEDMatrix](https://github.com/ChuckBuilds/LEDMatrix),
made for kids. Every time it comes round it shows a different scene, and every scene moves.

![All eight scenes, animated](docs/preview.gif)

## The scenes

They take turns in this order, so the two elf scenes never come one after the other.

![Sleigh, elves, snowman, presents, gingerbread, workshop, lights, chimney](docs/scenes.png)

| Scene | What moves |
| --- | --- |
| `sleigh` | Santa flies by with a teetering tower of presents in his sleigh and four reindeer. He waves, the tower wobbles, the legs gallop, the team bobs, and Rudolph's bright red nose glows. |
| `elves` | The elves hop and toss presents, and one throws a present in a high arc across the whole card to the elf on the other side -- a new present, in a new colour, every throw. |
| `snowman` | Snow falls and two snowmen wave. |
| `presents` | Two trees with blinking ornaments and twinkling stars, and the presents take turns bouncing. |
| `gingerbread` | Six gingerbread men dance, three on each side. |
| `workshop` | Elves build a present at their bench, one step at a time: one hammers the box together, the other ties on the ribbon and bow, it sparkles when it is done, and the next one starts. |
| `lights` | Strings of bulbs chase along the top and bottom, the number flashes colours, and the words stretch the width of the card, every letter flashing. |
| `chimney` | Santa is stuck in the chimney with his legs in the air, kicking in turn, while snow falls and the window flickers. |

Each one shows the days left (`47 DAYS TILL CHRISTMAS`), `1 DAY` on Christmas Eve and
`MERRY CHRISTMAS!` on the day itself.

Every picture here was drawn by the plugin's own code at 256 × 32 LEDs, one pixel per LED.
The plugin loads no image files: all the art is code, in `santa_scenes.py`.

## Settings

| Setting | Default | |
| --- | --- | --- |
| `enabled` | `false` | Show it. |
| `display_duration` | `15` | Seconds on screen in normal rotation. |
| `scenes` | all eight | Which scenes to show. |
| `order` | `in_turn` | `in_turn` goes through them one after another; `random` picks a different one each time, never the one just shown. |
| `season_start` | `11-01` | Month-day to start showing. It stays up through Christmas Day and shows nothing the rest of the year, so it can stay enabled all year. |
| `animation_fps` | `6` | Animation steps per second in normal rotation. |
| `vegas_animation_hz` | `1` | Animation steps per second while it scrolls in Vegas mode. See below. |

## In Vegas mode

The card joins the scroll like any other plugin, and the scroll carries it the length of the
display, so the sleigh really flies across. It is a *live element* (LEDMatrix 3.8.0 and later):
the ticker redraws it in place while it is on screen, so the legs gallop and the snow falls as it
moves. On older versions it scrolls as a still picture.

The ticker caps how often it redraws a live element: **once a second** with the stock
`rgbmatrix` Python binding, faster with the rebuilt one (LEDMatrix's
`scripts/build_rgbmatrix_nogil.sh`). Keep `vegas_animation_hz` at that cap, so that every
redraw is a new step of the animation.

Each lap of the scroll gets the next scene, even when Santa's Countdown is the only thing in the
rotation.

## Panel sizes

Drawn for 32-row panels. On a 256-wide display everything fits. Narrower panels keep the main
character and shrink the words: `47 DAYS` at 128, `47` alone at 64. Taller panels get the picture
scaled up whole, as far as leaves at least 64 columns to draw in (128×64 doubles the 64-wide card;
64×64 shows the 64-wide card centred).

## Install

By URL, in the web interface's plugin manager (install from URL):
`https://github.com/BigC07/ledmatrix-santa-countdown`. It is not in the Plugin Store yet. No API
keys, no network, no extra packages.

## Tested

On a Raspberry Pi 4 driving four 64×32 panels (256×32) in Vegas scroll mode, in the rotation
with sports, F1, a clock and weather cards, and on its own. LEDMatrix's safety harness
(`scripts/check_plugin.py`) passes at 64×32, 128×32, 64×64, 96×48, 128×64, 256×32, 128×96 and
256×128, and its Vegas live-element check passes too.

## License

GPL-3.0. All of the code and art is original to this plugin.
