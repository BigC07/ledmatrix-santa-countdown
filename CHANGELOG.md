# Changelog

## [Unreleased]

- A ninth scene, `loading`: elves load Santa's parked sleigh one present at a
  time until the tower is full, then hop while it sparkles. It comes between
  the snowman and the presents, so no two elf scenes are ever back to back.
- A tenth scene, `tree`: Santa hangs the low ornaments, an elf on a ladder
  the high ones and the star, then the tree lights up. It comes between the
  lights and the chimney.
- An eleventh scene, `clock`: the time in rolling candy-cane stripes, ticking
  every second while it scrolls, with the date and the days to go. New setting
  `time_format` (12h, the default, or 24h).
- The star on every tree is a seven-wide gold star, steady, instead of a
  five-pixel plus that flashed white and gold and read as a cross.
- The snowmen are bigger, nearly the card's height, and their hat shows: grey
  with a red band and holly, where it was black (an unlit LED).

## [1.0.1] - 2026-11-08

- Taller panels: the rows above and below the card get the scene's sky,
  falling snow or twinkling stars, instead of plain black; the snowman's ground
  runs to the bottom of the panel.
- A doubled card always keeps at least 64 columns: a 64x64 panel shows the
  64-wide card, not a cramped 32-wide one.
- The workshop fits narrow panels: one elf at a short bench below 96 columns,
  both elves from 96.

## [1.0.0] - 2026-11-08

First release.

- Eight animated scenes, all drawn in code: Santa waving from a sleigh with a
  teetering tower of presents, behind four reindeer (Rudolph's nose glows, the legs gallop), two waving snowmen in falling
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
  repeating the last one. The two elf scenes never come back to back.
- Shows from `season_start` (1 November by default) through Christmas Day, and
  nothing the rest of the year.
- Vegas scroll: one live element the ticker redraws in place, so the card
  animates while it crosses the panel (core 3.8.0+; older cores get a still
  frame). It moves to the next scene every lap, even when nothing else is in
  the rotation.
- Fits 64, 128 and 256-wide panels (the words shrink to `47 DAYS`, then `47`),
  and scales up whole on 64-high panels.
