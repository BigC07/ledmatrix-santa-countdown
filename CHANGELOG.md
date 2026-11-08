# Changelog

## [1.0.0] - 2026-11-08

First release.

- Eight animated scenes, all drawn in code: Santa's sleigh and four reindeer
  (Rudolph's nose glows, the legs gallop), two waving snowmen in falling
  snow, trees with blinking ornaments and bouncing presents, six dancing
  gingerbread men, strings of chasing lights top and bottom with flashing
  letters, Santa stuck in a chimney kicking his legs, elves who throw a
  present across the whole card, and elves building a present in their
  workshop.
- Snow and stars fill the whole card, drawn last and kept a pixel clear of
  every letter and every character.
- Every scene fills the card: whatever room the words leave on the right gets
  a second tree, more dancers, the moon or another elf.
- The days left until Christmas in big digits, `1 DAY` on Christmas Eve and
  `MERRY CHRISTMAS!` on the day.
- A different scene each time it comes round: in turn, or at random without
  repeating the last one.
- Shows from `season_start` (1 November by default) through Christmas Day, and
  nothing the rest of the year.
- Vegas scroll: one live element the ticker redraws in place, so the card
  animates while it crosses the panel (core 3.8.0+; older cores get a still
  frame). It moves to the next scene every lap, even when nothing else is in
  the rotation.
- Fits 64, 128 and 256-wide panels (the words shrink to `47 DAYS`, then `47`),
  and scales up whole on 64-high panels.
